import logging
from pathlib import Path
from typing import List

from Code.app_vars import AppConfig
from Code.xml_object import (XMLComment, XMLElement, XMLObject,
                             XMLParserException)

from .dataclasses import Dependencie, Identifier, Metadata, ModUnit

logger = logging.getLogger("Loader")


class Loader:
    active_mod: List[ModUnit] = []
    inactive_mod: List[ModUnit] = []

    @staticmethod
    def init_data_load():
        game_path = AppConfig.get("barotrauma_dir", None)

        if game_path is None:
            logger.error("Game path not set!")
            return
        else:
            game_path = Path(game_path)

        if not game_path.exists():
            logger.error(f"Game path dont exists!\n|Path: {game_path}")
            return

        Loader.load_user_config(game_path / "config_player.xml")
        Loader.load_lua_config(game_path)

    @staticmethod
    def load_user_config(path_to_config_player: Path):
        if not path_to_config_player.exists():
            logger.error(
                f"config_player.xml path dont exists!\n|Path: {path_to_config_player}"
            )
            return

        obj = XMLObject.load_file(path_to_config_player)
        if not obj.root:
            logger.error(f"Invalid config_player.xml!\n|Path: {path_to_config_player}")

        packages = obj.find("package")

        i = 1
        for package in packages:
            if isinstance(package, XMLComment):
                continue

            elif package.name == "package":
                path = package.attributes.get("path", None)
                if path is None:
                    continue

                path = Path(path).parent
                mod = ModUnit.build_by_path(path)
                if mod is None:
                    logger.error(f"Can not build mod whith path:{path}")
                    continue

                mod.load_order = i
                Loader.active_mod.append(mod)
                i += 1

    @staticmethod
    def load_lua_config(path_to_game: Path):
        if not path_to_game.exists():
            logger.error(f"Game path does not exist: {path_to_game}")
            return

        config_path = path_to_game / "LuaCsSetupConfig.xml"
        if config_path.exists():
            xml_obj = XMLObject.load_file(config_path).root
            has_cs = (
                xml_obj.attributes.get("EnableCsScripting", "false").lower() == "true"
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
