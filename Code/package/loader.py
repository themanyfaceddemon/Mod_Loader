import atexit
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.dom import minidom

from Code.app_vars import AppGlobalsAndConfig

from .package import Package

logger = logging.getLogger("ModLoader")


class ModLoader:
    active_mods: List[Package] = []
    inactive_mods: List[Package] = []

    @classmethod
    def init(cls) -> None:
        cls.load()
        atexit.register(cls.save_mods)

    @classmethod
    def _find_package_by_id(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.active_mods + cls.inactive_mods:
            if pkg.identifier.id == package_id:
                return pkg
        return None

    @classmethod
    def _sort_active_mods_by_load_order(cls) -> List[Package]:
        return sorted(
            cls.active_mods,
            key=lambda pkg: (pkg.metadata.load_order is None, pkg.metadata.load_order),
        )

    @classmethod
    def _add_dependencies_from_inactive(cls) -> None:
        active_ids = {pkg.identifier.id for pkg in cls.active_mods}

        for pkg in list(cls.active_mods):
            for req in pkg.metadata.requirements:
                if req.id not in active_ids:
                    dep_pkg = cls._find_package_by_id(req.id)
                    if dep_pkg and dep_pkg in cls.inactive_mods:
                        cls.active_mods.append(dep_pkg)
                        cls.inactive_mods.remove(dep_pkg)
                        active_ids.add(dep_pkg.identifier.id)

            for patch in pkg.metadata.patches:
                if patch.id not in active_ids:
                    dep_pkg = cls._find_package_by_id(patch.id)
                    if dep_pkg and dep_pkg in cls.inactive_mods:
                        cls.active_mods.append(dep_pkg)
                        cls.inactive_mods.remove(dep_pkg)
                        active_ids.add(dep_pkg.identifier.id)

    @classmethod
    def _build_dependency_graph(cls) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        graph: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {pkg.identifier.id: 0 for pkg in cls.active_mods}

        def add_dependency(package_id: str, dependency_id: str) -> None:
            if dependency_id in indegree:
                graph[dependency_id].append(package_id)
                indegree[package_id] += 1

        for pkg in cls.active_mods:
            current_id = pkg.identifier.id
            for req in pkg.metadata.requirements:
                add_dependency(current_id, req.id)
            for patch in pkg.metadata.patches:
                add_dependency(patch.id, current_id)
            for opt_req in pkg.metadata.optionals_requirements:
                if opt_req.id in indegree:
                    add_dependency(current_id, opt_req.id)
            for opt_patch in pkg.metadata.optionals_patches:
                if opt_patch.id in indegree:
                    add_dependency(opt_patch.id, current_id)

        return graph, indegree

    @classmethod
    def _topological_sort(
        cls,
        graph: Dict[str, List[str]],
        indegree: Dict[str, int],
    ) -> List[Package]:
        queue: deque[str] = deque(
            [pkg_id for pkg_id, deg in indegree.items() if deg == 0]
        )
        final_sorted_packages: List[Package] = []

        while queue:
            sorted_level = sorted(
                (
                    pkg_id
                    for pkg_id in queue
                    if cls._find_package_by_id(pkg_id) is not None
                ),
                key=lambda pkg_id: cls._find_package_by_id(pkg_id).identifier.name,  # type: ignore
            )
            queue = deque(sorted_level)

            for current_id in list(queue):
                queue.popleft()
                current_pkg = cls._find_package_by_id(current_id)
                if current_pkg:
                    final_sorted_packages.append(current_pkg)
                else:
                    raise ValueError(
                        f"Package with id '{current_id}' not found in active mods or inactive mods"
                    )

                for neighbor in graph[current_id]:
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        queue.append(neighbor)

        if len(final_sorted_packages) != len(indegree):
            raise ValueError("Unable to resolve dependencies: cycle detected.")

        return final_sorted_packages

    @classmethod
    def process_errors(cls) -> None:
        install_lua = AppGlobalsAndConfig.get("has_lua", False)
        install_cs = AppGlobalsAndConfig.get("enable_cs_scripting", False)
        active_ids = {pkg.identifier.id for pkg in cls.active_mods}

        for pkg in cls.active_mods + cls.inactive_mods:
            pkg.metadata.errors.clear()
            pkg.metadata.warnings.clear()
            pkg.parse_metadata()

            for conflict in pkg.metadata.conflicts:
                if conflict.id in active_ids:
                    if conflict.level == "error":
                        pkg.metadata.errors.append(conflict.message)

                    elif conflict.level == "warning":
                        pkg.metadata.warnings.append(conflict.message)

            if pkg.metadata.has_cs or pkg.metadata.has_dll:
                if not install_cs and not pkg.metadata.settings.get(
                    "DisableCSDLLCheck", False
                ):
                    pkg.metadata.errors.append(
                        "The mod uses .dll or .cs, but you do not have the flag for using the cs script set"
                    )

            if pkg.metadata.has_lua:
                if not install_lua and not pkg.metadata.settings.get(
                    "IgnoreLUACheck", False
                ):
                    pkg.metadata.errors.append(
                        "The mod uses lua, but you don't have lua installed."
                    )

    @classmethod
    def sort(cls) -> None:
        cls.active_mods = cls._sort_active_mods_by_load_order()
        cls._add_dependencies_from_inactive()
        graph, indegree = cls._build_dependency_graph()
        cls.active_mods = cls._topological_sort(graph, indegree)

        for index, mod in enumerate(cls.active_mods):
            mod.metadata.load_order = index + 1

        cls.process_errors()

    @classmethod
    def add_to_active(cls, package: Package, position: Optional[int] = None) -> None:
        if cls._find_package_by_id(package.identifier.id):
            return

        if position is not None and 0 <= position < len(cls.active_mods):
            cls.active_mods.insert(position, package)
        else:
            cls.active_mods.append(package)

    @classmethod
    def remove_from_active(cls, package_id: str) -> bool:
        for pkg in cls.active_mods:
            if pkg.identifier.id == package_id:
                cls.active_mods.remove(pkg)
                return True

        return False

    @classmethod
    def remove_from_inactive(cls, package_id: str) -> bool:
        for pkg in cls.inactive_mods:
            if pkg.identifier.id == package_id:
                cls.inactive_mods.remove(pkg)
                return True

        return False

    @classmethod
    def add_to_inactive(cls, package: Package) -> None:
        if cls._find_package_by_id(package.identifier.id):
            return

        if package not in cls.inactive_mods:
            cls.inactive_mods.append(package)

    @classmethod
    def find_in_active(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.active_mods:
            if pkg.identifier.id == package_id:
                return pkg

        return None

    @classmethod
    def find_in_inactive(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.inactive_mods:
            if pkg.identifier.id == package_id:
                return pkg

        return None

    @classmethod
    def toggle_mod(cls, package_id: str) -> bool:
        package = cls.find_in_active(package_id)
        if package:
            cls.remove_from_active(package_id)
            cls.add_to_inactive(package)
            return True

        else:
            package = cls.find_in_inactive(package_id)
            if package:
                cls.remove_from_inactive(package_id)
                cls.add_to_active(package)
                return True

        return False

    @classmethod
    def activate_mod(cls, package_id: str) -> bool:
        package = cls.find_in_inactive(package_id)
        if package:
            cls.remove_from_inactive(package_id)
            cls.add_to_active(package)
            return True

        return False

    @classmethod
    def deactivate_mod(cls, package_id: str) -> bool:
        package = cls.find_in_active(package_id)
        if package:
            cls.remove_from_active(package_id)
            cls.add_to_inactive(package)
            return True

        return False

    @classmethod
    def move_active_mod(cls, package_id: str, new_position: int) -> bool:
        if new_position < 0 or new_position >= len(cls.active_mods):
            logger.error(
                f"Invalid position {new_position}. Must be within the range of active mods."
            )
            return False

        current_position = next(
            (
                i
                for i, pkg in enumerate(cls.active_mods)
                if pkg.identifier.id == package_id
            ),
            None,
        )
        if current_position is None:
            logger.warning(f"Mod with id '{package_id}' not found in active mods.")
            return False

        mod = cls.active_mods.pop(current_position)
        cls.active_mods.insert(new_position, mod)

        for index, mod in enumerate(cls.active_mods):
            mod.metadata.load_order = index + 1

        return True

    @classmethod
    def swap_active_mods(cls, package_id: str, target_package_id: str) -> bool:
        index1 = next(
            (
                i
                for i, pkg in enumerate(cls.active_mods)
                if pkg.identifier.id == package_id
            ),
            None,
        )
        index2 = next(
            (
                i
                for i, pkg in enumerate(cls.active_mods)
                if pkg.identifier.id == target_package_id
            ),
            None,
        )

        if index1 is None or index2 is None:
            logger.warning(
                f"Cannot swap active mods: '{package_id}' or '{target_package_id}' not found."
            )
            return False

        cls.active_mods[index1], cls.active_mods[index2] = (
            cls.active_mods[index2],
            cls.active_mods[index1],
        )
        return True

    @classmethod
    def swap_inactive_mods(cls, package_id: str, target_package_id: str) -> bool:
        index1 = next(
            (
                i
                for i, pkg in enumerate(cls.inactive_mods)
                if pkg.identifier.id == package_id
            ),
            None,
        )
        index2 = next(
            (
                i
                for i, pkg in enumerate(cls.inactive_mods)
                if pkg.identifier.id == target_package_id
            ),
            None,
        )

        if index1 is None or index2 is None:
            logger.warning(
                f"Cannot swap inactive mods: '{package_id}' or '{target_package_id}' not found."
            )
            return False

        cls.inactive_mods[index1], cls.inactive_mods[index2] = (
            cls.inactive_mods[index2],
            cls.inactive_mods[index1],
        )
        return True

    @classmethod
    def move_active_mod_to_end(cls, package_id: str) -> bool:
        current_index = next(
            (
                i
                for i, pkg in enumerate(cls.active_mods)
                if pkg.identifier.id == package_id
            ),
            None,
        )
        if current_index is None:
            return False

        mod = cls.active_mods.pop(current_index)
        cls.active_mods.append(mod)
        return True

    @classmethod
    def move_inactive_mod_to_end(cls, package_id: str) -> bool:
        current_index = next(
            (
                i
                for i, pkg in enumerate(cls.inactive_mods)
                if pkg.identifier.id == package_id
            ),
            None,
        )
        if current_index is None:
            return False

        mod = cls.inactive_mods.pop(current_index)
        cls.inactive_mods.append(mod)
        return True

    @classmethod
    def load(cls) -> None:
        game_path = cls._get_game_path()
        if game_path is None:
            return

        cls._load_local_mods(game_path)
        config_player_path = game_path / "config_player.xml"
        if not config_player_path.exists():
            logger.error(
                f"config_player.xml does not exist!\n| Path: {config_player_path}"
            )
            return

        tree = ET.parse(str(config_player_path))
        root = tree.getroot()
        content_packages = root.find(".//contentpackages")
        if content_packages is None:
            logger.error("Invalid XML structure: <contentpackages> not found.")
            return

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            logger.error(
                "Invalid XML structure: <regularpackages> not found inside <contentpackages>."
            )
            return

        cls._load_regular_packages(regular_packages, game_path)
        cls._set_install_mod_dir(regular_packages, config_player_path)
        install_mod_path = AppGlobalsAndConfig.get("barotrauma_install_mod_dir")
        if install_mod_path:
            cls._load_installed_mods(Path(install_mod_path))

        barotrauma_deps_json = game_path / "Barotrauma.deps.json"

        with open(barotrauma_deps_json, "r", encoding="utf-8") as file:
            content = file.read()
            if "Luatrauma" in content:
                AppGlobalsAndConfig.set("has_lua", True)
            else:
                AppGlobalsAndConfig.set("has_lua", False)

        lua_config = game_path / "LuaCsSetupConfig.xml"
        if not lua_config.exists():
            AppGlobalsAndConfig.set("enable_cs_scripting", False)
            return

        tree = ET.parse(str(lua_config))
        root = tree.getroot()
        enable_cs_scripting = root.attrib.get("EnableCsScripting", "false").lower()
        AppGlobalsAndConfig.set("enable_cs_scripting", enable_cs_scripting == "true")

    @classmethod
    def _get_game_path(cls) -> Optional[Path]:
        game_path = AppGlobalsAndConfig.get("barotrauma_dir")
        if game_path is None:
            logger.error("Game path not set in AppGlobalsAndConfig.")
            return None

        return Path(game_path)

    @classmethod
    def _load_local_mods(cls, game_path: Path) -> None:
        local_mods_path = game_path / "LocalMods"
        if local_mods_path.exists():
            for dir in local_mods_path.iterdir():
                if dir.is_dir() and not dir.name.startswith("."):
                    obj = Package(dir)
                    obj.metadata.local = True
                    cls.add_to_inactive(obj)

    @classmethod
    def _load_regular_packages(
        cls, regular_packages: ET.Element, game_path: Path
    ) -> None:
        for pack_element in regular_packages:
            pack_path = pack_element.attrib.get("path")
            if pack_path is None:
                logger.warning("Path for package not found!")
                continue

            if pack_path.startswith("LocalMods"):
                pack_path = game_path / pack_path

            pack_path = Path(pack_path).parent
            obj = Package(pack_path)
            if not cls.activate_mod(obj.identifier.id):
                cls.add_to_active(obj)

    @classmethod
    def _set_install_mod_dir(
        cls, regular_packages: ET.Element, config_player_path: Path
    ) -> None:
        if not AppGlobalsAndConfig.get("barotrauma_install_mod_dir"):
            for pack_element in regular_packages:
                pack_path = pack_element.attrib.get("path")
                if pack_path and not pack_path.startswith("LocalMods"):
                    AppGlobalsAndConfig.set(
                        "barotrauma_install_mod_dir",
                        str(Path(pack_path).parent.parent),
                    )
                    break

    @classmethod
    def _load_installed_mods(cls, install_mod_path: Path) -> None:
        if install_mod_path.exists():
            for mod_path in install_mod_path.iterdir():
                if mod_path.is_dir():
                    try:
                        obj = Package(mod_path)
                    except Exception as err:
                        logger.error(f"Failed to load mod from {mod_path}: {err}")
                        continue

                    if not cls._find_package_by_id(obj.identifier.id):
                        cls.add_to_inactive(obj)

    @classmethod
    def save_mods(cls) -> None:
        unique_mods = {pkg.identifier.id: pkg for pkg in cls.active_mods}.values()
        cls.active_mods = list(unique_mods)

        game_path = cls._get_game_path()
        if game_path is None:
            return

        config_player_path = game_path / "config_player.xml"
        if not config_player_path.exists():
            logger.error(
                f"config_player.xml does not exist!\n| Path: {config_player_path}"
            )
            return

        tree = ET.parse(str(config_player_path))
        root = tree.getroot()
        content_packages = root.find(".//contentpackages")
        if content_packages is None:
            logger.error("Invalid XML structure: <contentpackages> not found.")
            return

        regular_packages = cls._prepare_regular_packages(content_packages)

        for mod in cls.active_mods:
            mod_path = mod.path
            mod_name = mod.identifier.name
            comment = ET.Comment(f"{mod_name}")
            regular_packages.append(comment)
            pack_element = ET.SubElement(regular_packages, "package")
            if mod.metadata.local:
                mod_path = str(
                    Path(*mod_path.parts[mod_path.parts.index("LocalMods") :])
                    / "filelist.xml"
                )
            else:
                mod_path = str(mod_path / "filelist.xml")

            pack_element.set("path", mod_path)

        cls._save_formatted_xml(tree, config_player_path)

    @classmethod
    def _prepare_regular_packages(cls, content_packages: ET.Element) -> ET.Element:
        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            regular_packages = ET.SubElement(content_packages, "regularpackages")
        else:
            for elem in list(regular_packages):
                regular_packages.remove(elem)

        return regular_packages

    @classmethod
    def _save_formatted_xml(
        cls, tree: ET.ElementTree, config_player_path: Path
    ) -> None:
        rough_string = ET.tostring(tree.getroot(), "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml_as_string = "\n".join(
            [line for line in reparsed.toprettyxml().splitlines() if line.strip()]
        )
        with open(config_player_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml_as_string)

        logger.info(f"Active mods saved to config_player.xml at {config_player_path}")
