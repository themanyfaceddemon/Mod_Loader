from pathlib import Path
from typing import List
from .dataclasses import Identifier, Dependencie, Metadata, ModUnit
from Code.app_vars import AppConfig
import logging
from Code.xml_object import XMLObject, XMLComment, XMLElement, XMLParserException

logger = logging.getLogger("Loader")


class Loader:
    active_mod: List[ModUnit]
    inactive_mod: List[ModUnit]

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

        regular_packages = obj.find("regularpackages")
        if not regular_packages:
            return  # TODO: It's too bad we didn't find any regular packages. That's going to be a problem.

        regular_packages = regular_packages[0]

        if isinstance(regular_packages, XMLComment):
            return

        i = 1
        for package in regular_packages.children:
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
            logger.error(f"Game path dont exists!\n|Path: {path_to_game}")
            return
