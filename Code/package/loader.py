import atexit
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from Code.app_vars import AppGlobalsAndConfig

from .package import Package


class PackageLoader:
    _active_packages: List[Package] = []
    found_first_package = False
    LUA_STEAM_ID: str = "2559634234"

    @staticmethod
    def init():
        atexit.register(PackageLoader.save_on_exit)

    @staticmethod
    def load(file_path: str) -> None:
        PackageLoader._active_packages.clear()
        PackageLoader._process_xml(Path(file_path))

    @staticmethod
    def save_on_exit() -> None:
        path = AppGlobalsAndConfig.get_config("barotrauma_dir_path")
        if path:
            PackageLoader.save(path + "/config_player.xml")

    @staticmethod
    def save(file_path: str) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        regular_packages = content_packages.find("regularpackages")  # type: ignore

        if regular_packages is not None:
            for child in list(regular_packages):
                regular_packages.remove(child)
        else:
            regular_packages = ET.SubElement(content_packages, "regularpackages")  # type: ignore

        filtered_packages = [
            pkg for pkg in PackageLoader._active_packages if pkg.order is not None
        ]
        for package in sorted(filtered_packages, key=lambda p: p.order):  # type: ignore
            regular_packages.append(ET.Comment(package.name))
            package_element = ET.SubElement(regular_packages, "package")
            package_element.set("path", str(package.path) + "\\filelist.xml")

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ", level=0)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _parse_package(package_path: Path, local_load: bool, order: int) -> Package:
        filelist_path = package_path / "filelist.xml"
        if not filelist_path.exists():
            raise ValueError(f"File {filelist_path} not found")

        tree = ET.parse(filelist_path)
        root = tree.getroot()

        if root.tag != "contentpackage":
            raise ValueError(f"contentpackage in {filelist_path} not found")

        return Package(
            name=root.get("name", "Error"),
            steamID=root.get("steamworkshopid", None),
            path=package_path,
            local=local_load,
            order=order,
        )

    @staticmethod
    def _process_xml(file_path: Path) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        if content_packages is None:
            return

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            raise ValueError("Not found <regularpackages>")

        PackageLoader._load_packages(regular_packages)

    @staticmethod
    def _load_packages(regular_packages: ET.Element) -> None:
        order = 0
        for package in regular_packages.findall("package"):
            order += 1
            package_path = package.get("path")
            if package_path:
                path = Path(package_path)

                local_load = str(path).startswith("LocalMods")
                PackageLoader._active_packages.append(
                    PackageLoader._parse_package(path.parent, local_load, order)
                )

    @staticmethod
    def sort_packages() -> List[Package]:
        always_first_package: Optional[Package] = None
        for pkg in PackageLoader._active_packages:
            if pkg.steamID == PackageLoader.LUA_STEAM_ID:
                always_first_package = pkg
                break

        if always_first_package:
            PackageLoader._active_packages.remove(always_first_package)
            PackageLoader.found_first_package = True
        else:
            PackageLoader.found_first_package = False

        dependency_graph = {pkg.name: set() for pkg in PackageLoader._active_packages}
        for package in PackageLoader._active_packages:
            for req_type in ["requirement", "optional"]:
                for dep_name in package.dependencies.get(req_type, {}):
                    dependency_graph[package.name].add(dep_name)
            for patch_name in package.dependencies.get("patch", {}):
                if patch_name in dependency_graph:
                    dependency_graph[patch_name].add(package.name)

        visited = set()
        sorted_packages = []
        cycle_detected = set()

        def topological_sort(package_name: str):
            if package_name in cycle_detected:
                raise ValueError(f"Циклическая зависимость с пакетом: {package_name}")
            if package_name not in visited:
                cycle_detected.add(package_name)
                for dep_name in dependency_graph[package_name]:
                    if dep_name in dependency_graph:
                        topological_sort(dep_name)
                cycle_detected.remove(package_name)
                visited.add(package_name)
                sorted_packages.append(package_name)

        for package in PackageLoader._active_packages:
            topological_sort(package.name)

        sorted_packages = sorted(sorted_packages, key=lambda name: name.lower())

        final_sorted_packages = [
            pkg for pkg in PackageLoader._active_packages if pkg.name in sorted_packages
        ]

        if always_first_package:
            final_sorted_packages.insert(0, always_first_package)

        for index, pkg in enumerate(final_sorted_packages):
            if pkg.order is not None:
                pkg.order = index

        return final_sorted_packages
