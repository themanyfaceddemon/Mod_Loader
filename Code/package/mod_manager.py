import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from Code.app_vars import AppConfig
from Code.xml_object import XMLObject

from .dataclasses import ModUnit

logger = logging.getLogger("ModManager")


class ModManager:
    active_mods: List[ModUnit] = []
    inactive_mods: List[ModUnit] = []

    @staticmethod
    def load_mods_and_configs():
        ModManager.active_mods.clear()
        ModManager.inactive_mods.clear()

        game_path = AppConfig.get("barotrauma_dir", None)

        if game_path is None:
            logger.error("Game path not set!")
            return
        else:
            game_path = Path(game_path)

        if not game_path.exists():
            logger.error(f"Game path dont exists!\n|Path: {game_path}")
            return

        ModManager.load_active_mods(game_path / "config_player.xml")
        ModManager.load_inactive_mods(AppConfig.get("barotrauma_install_mod_dir"))
        ModManager.load_lua_config(game_path)

    @staticmethod
    def load_active_mods(path_to_config_player: Path):
        if not path_to_config_player.exists():
            logger.error(
                f"config_player.xml path doesn't exist!\n|Path: {path_to_config_player}"
            )
            return

        obj = XMLObject.load_file(path_to_config_player)
        if not obj.root:
            logger.error(f"Invalid config_player.xml!\n|Path: {path_to_config_player}")
            return

        obj = obj.root

        packages = obj.find_only_elements("package")

        package_paths = [
            (i, package.attributes.get("path", None))
            for i, package in enumerate(packages, start=1)
            if package.name == "package" and package.attributes.get("path", None)
        ]

        def process_package(index, path):
            try:
                path = Path(path).parent
                mod = ModUnit.build_by_path(path)
                if mod is None:
                    logger.error(f"Cannot build mod with path: {path}")
                    return None

                mod.load_order = index
                return mod

            except Exception as err:
                logger.error(err)
                return None

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_package, index, path)
                for index, path in package_paths
            ]

            for future in as_completed(futures):
                mod = future.result()
                if mod is not None:
                    ModManager.active_mods.append(mod)

        ModManager.active_mods.sort(key=lambda m: m.load_order)  # type: ignore
        for index, mod in enumerate(ModManager.active_mods, start=1):
            mod.load_order = index

    @staticmethod
    def load_inactive_mods(path_to_all_mods: Optional[str]):
        if path_to_all_mods is None:
            logger.error("Barotrauma mod dir not set!")
            return

        package_paths = [
            path for path in Path(path_to_all_mods).iterdir() if path.is_dir()
        ]

        def process_package(path):
            try:
                mod = ModUnit.build_by_path(path)
                if mod is None:
                    logger.error(f"Cannot build mod with path: {path}")
                    return None
                return mod

            except Exception as err:
                logger.error(err)
                return None

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_package, path) for path in package_paths]
            for future in as_completed(futures):
                mod = future.result()
                if mod is not None:
                    ModManager.inactive_mods.append(mod)

    @staticmethod
    def load_lua_config(path_to_game: Path):
        if not path_to_game.exists():
            logger.error(f"Game path does not exist: {path_to_game}")
            return

        config_path = path_to_game / "LuaCsSetupConfig.xml"
        if config_path.exists():
            xml_obj = XMLObject.load_file(config_path).root
            has_cs = (
                xml_obj.attributes.get("enablecsscripting", "false").lower() == "true"
                if xml_obj
                else False
            )
            AppConfig.set("has_cs", has_cs)
            logger.debug(f"CS scripting enabled: {has_cs}")

        else:
            AppConfig.set("has_cs", False)
            logger.debug("LuaCsSetupConfig.xml not found, disabling CS scripting.")

        lua_dep_path = path_to_game / "Barotrauma.deps.json"
        if lua_dep_path.exists():
            with open(lua_dep_path, "r", encoding="utf-8") as file:
                has_lua = "Luatrauma" in file.read()
                AppConfig.set("has_lua", has_lua)
                logger.debug(f"Lua support enabled: {has_lua}")

        else:
            AppConfig.set("has_lua", False)
            logger.debug("Barotrauma.deps.json not found, disabling Lua support.")

    @staticmethod
    def find_mod_by_id(mod_id: str) -> Optional[ModUnit]:
        for mod in ModManager.active_mods + ModManager.inactive_mods:
            if mod.id == mod_id:
                return mod

        return None

    @staticmethod
    def activate_mod(mod: ModUnit) -> None:
        if mod in ModManager.inactive_mods:
            ModManager.inactive_mods.remove(mod)
            ModManager.active_mods.append(mod)

    @staticmethod
    def deactivate_mod(mod: ModUnit) -> None:
        if mod in ModManager.active_mods:
            ModManager.active_mods.remove(mod)
            ModManager.inactive_mods.append(mod)

    @staticmethod
    def swap_active_mods(mod1: ModUnit, mod2: ModUnit) -> None:
        try:
            idx1, idx2 = (
                ModManager.active_mods.index(mod1),
                ModManager.active_mods.index(mod2),
            )
            ModManager.active_mods[idx1], ModManager.active_mods[idx2] = (
                ModManager.active_mods[idx2],
                ModManager.active_mods[idx1],
            )

        except ValueError:
            pass

    @staticmethod
    def swap_inactive_mods(mod1: ModUnit, mod2: ModUnit) -> None:
        try:
            idx1, idx2 = (
                ModManager.inactive_mods.index(mod1),
                ModManager.inactive_mods.index(mod2),
            )
            ModManager.inactive_mods[idx1], ModManager.inactive_mods[idx2] = (
                ModManager.inactive_mods[idx2],
                ModManager.inactive_mods[idx1],
            )

        except ValueError:
            pass

    @staticmethod
    def move_active_mod_to_end(mod: ModUnit) -> None:
        if mod in ModManager.active_mods:
            ModManager.active_mods.remove(mod)
            ModManager.active_mods.append(mod)

    @staticmethod
    def move_inactive_mod_to_end(mod: ModUnit) -> None:
        if mod in ModManager.inactive_mods:
            ModManager.inactive_mods.remove(mod)
            ModManager.inactive_mods.append(mod)
