import atexit
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from Code.app_vars import AppGlobalsAndConfig

from .package import Package

logger = logging.getLogger("PackageLoader")


class PackageLoader:
    LUA_STEAM_ID: str = "2559634234"
    _active_packages: List[Package] = []
    _internal_dependency_library: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
    found_first_package: bool = False

    @classmethod
    def init(cls) -> None:
        atexit.register(cls.save_on_exit)
        cls.load_internal_dependency_library()

    @classmethod
    def load_internal_dependency_library(cls) -> None:
        file_path = AppGlobalsAndConfig.get_data_root() / "internal_dependencies.xml"
        try:
            cls._process_internal_dependencies(file_path)
        except FileNotFoundError:
            logger.error(f"Dependency file {file_path} not found.")

    @classmethod
    def _process_internal_dependencies(cls, file_path: Path) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()
        dependencies = root.findall("internal_dependencies")

        for dep in dependencies:
            steam_id = dep.get("steamID")
            if not steam_id:
                continue

            dep_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
            for dep_type in ["patch", "requirement", "optional", "conflict"]:
                dep_dict[dep_type] = cls._parse_internal_dependency(dep, dep_type)
            cls._internal_dependency_library[steam_id] = dep_dict

    @classmethod
    def _parse_internal_dependency(
        cls, dep_element: ET.Element, dep_type: str
    ) -> Dict[str, Dict[str, str]]:
        dep_type_element = dep_element.find(dep_type)
        dep_dict: Dict[str, Dict[str, str]] = {}

        if dep_type_element is not None:
            for mod in dep_type_element.findall("mod"):
                mod_info = {
                    "name": mod.get("name", ""),
                    "steamID": mod.get("steamID", ""),
                }
                dep_id = mod_info["steamID"] or mod_info["name"]
                if dep_id:
                    dep_dict[dep_id] = mod_info
        return dep_dict

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> None:
        cls._active_packages.clear()
        cls._process_xml(Path(file_path))

    @classmethod
    def save_on_exit(cls) -> None:
        path = AppGlobalsAndConfig.get_config("barotrauma_dir_path")
        if path:
            cls.save(Path(path) / "config_player.xml")

    @classmethod
    def save(cls, file_path: Path) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        if content_packages is None:
            raise ValueError("Content packages not found in the XML file.")

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is not None:
            regular_packages.clear()
        else:
            regular_packages = ET.SubElement(content_packages, "regularpackages")

        filtered_packages = [
            pkg for pkg in cls._active_packages if pkg.order is not None
        ]
        sorted_packages = sorted(filtered_packages, key=lambda p: p.order)  # type: ignore

        for package in sorted_packages:
            regular_packages.append(ET.Comment(package.name))
            package_element = ET.SubElement(regular_packages, "package")
            package_element.set("path", str(package.path / "filelist.xml"))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ", level=0)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    @classmethod
    def _parse_package(
        cls, package_path: Path, local_load: bool, order: int
    ) -> Package:
        filelist_path = package_path / "filelist.xml"
        if not filelist_path.exists():
            raise FileNotFoundError(f"File {filelist_path} not found.")

        tree = ET.parse(filelist_path)
        root = tree.getroot()

        if root.tag != "contentpackage":
            raise ValueError(
                f"Invalid root tag in {filelist_path}, expected 'contentpackage'."
            )

        return Package(
            name=root.get("name", "Error"),
            steamID=root.get("steamworkshopid"),
            path=package_path,
            local=local_load,
            order=order,
        )

    @classmethod
    def _process_xml(cls, file_path: Path) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        if content_packages is None:
            logger.warning("No 'contentpackages' element found in the XML file.")
            return

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            raise ValueError(
                "Element 'regularpackages' not found in 'contentpackages'."
            )

        cls._load_packages(regular_packages)

    @classmethod
    def _load_packages(cls, regular_packages: ET.Element) -> None:
        for order, package in enumerate(regular_packages.findall("package"), start=1):
            package_path_str = package.get("path")
            if not package_path_str:
                continue

            path = Path(package_path_str)
            local_load = path.parts[0] == "LocalMods"
            package_dir = path.parent
            try:
                parsed_package = cls._parse_package(package_dir, local_load, order)
                cls._active_packages.append(parsed_package)
            except (FileNotFoundError, ValueError) as e:
                logger.error(e)

    @classmethod
    def sort_packages(cls) -> List[Package]:
        always_first_package = cls._extract_lua_package()

        dependency_graph = cls._build_dependency_graph()

        try:
            sorted_packages = cls._topological_sort(dependency_graph)
        except ValueError as e:
            logger.error(e)
            # Сортируем пакеты алфавитно по имени при ошибке
            sorted_packages = sorted(cls._active_packages, key=lambda pkg: pkg.name)

        if always_first_package:
            sorted_packages.insert(0, always_first_package)

        for index, pkg in enumerate(sorted_packages):
            pkg.order = index

        return sorted_packages

    @classmethod
    def _extract_lua_package(cls) -> Optional[Package]:
        for pkg in cls._active_packages:
            if pkg.steamID == cls.LUA_STEAM_ID:
                cls._active_packages.remove(pkg)
                cls.found_first_package = True
                return pkg
        cls.found_first_package = False
        return None

    @classmethod
    def _build_dependency_graph(cls) -> Dict[Package, Set[Package]]:
        dependency_graph: Dict[Package, Set[Package]] = {
            pkg: set() for pkg in cls._active_packages
        }

        for package in cls._active_packages:
            package_dependencies = package.dependencies or {}

            if not package_dependencies and package.steamID:
                package_dependencies = cls._internal_dependency_library.get(
                    package.steamID, {}
                )

            for dep_type in ["requirement", "optional"]:
                dep_list = package_dependencies.get(dep_type, {})
                for dep_id in dep_list:
                    dep_pkg = cls._find_package_by_identifier(dep_id)
                    if dep_pkg:
                        dependency_graph[package].add(dep_pkg)
                    else:
                        logger.warning(
                            f"Dependency '{dep_id}' for package '{package.name}' not found among active packages."
                        )

            for dep_id in package_dependencies.get("patch", {}):
                dep_pkg = cls._find_package_by_identifier(dep_id)
                if dep_pkg:
                    dependency_graph[dep_pkg].add(package)
                else:
                    logger.warning(
                        f"Patch '{dep_id}' for package '{package.name}' not found among active packages."
                    )

        return dependency_graph

    @classmethod
    def _find_package_by_identifier(cls, identifier: str) -> Optional[Package]:
        for pkg in cls._active_packages:
            if pkg.get_identifier() == identifier:
                return pkg
        return None

    @classmethod
    def _topological_sort(
        cls, dependency_graph: Dict[Package, Set[Package]]
    ) -> List[Package]:
        visited: Set[Package] = set()
        sorted_packages: List[Package] = []
        temp_marks: Set[Package] = set()

        nodes = sorted(dependency_graph.keys(), key=lambda pkg: pkg.name)

        def visit(node: Package) -> None:
            if node in temp_marks:
                raise ValueError(f"Cyclic dependency detected: {node.name}")
            if node not in visited:
                temp_marks.add(node)
                neighbors = sorted(
                    dependency_graph.get(node, []), key=lambda pkg: pkg.name
                )
                for neighbor in neighbors:
                    visit(neighbor)
                temp_marks.remove(node)
                visited.add(node)
                sorted_packages.append(node)

        for node in nodes:
            if node not in visited:
                visit(node)

        return sorted_packages[::-1]
