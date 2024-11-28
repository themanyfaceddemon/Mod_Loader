import logging
import threading
from pathlib import Path

import dearpygui.dearpygui as dpg

from Code.app_vars import AppConfig
from Code.game import Game
from Code.loc import Localization as loc
from Code.package import ModManager

logger = logging.getLogger("BarotraumaPathProcessor")


class BarotraumaWindow:
    @staticmethod
    def create_window():
        from .app_interface import AppInterface

        if dpg.does_item_exist("baro_window"):
            dpg.delete_item("baro_window")

        with dpg.window(
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_title_bar=True,
            tag="baro_window",
        ):
            dpg.add_text(
                loc.get_string("label-barotrauma-path-settings"), color=(200, 200, 250)
            )

            dpg.add_input_text(
                hint=loc.get_string("hint-enter-barotrauma-path"),
                callback=BarotraumaWindow.validate_barotrauma_path,
                tag="barotrauma_input_path",
                width=300,
            )

            with dpg.group(horizontal=True):
                dpg.add_text(
                    loc.get_string("label-current-path"), color=(100, 150, 250)
                )
                dpg.add_text(
                    AppConfig.get("barotrauma_dir", loc.get_string("base-not-set")),  # type: ignore
                    tag="barotrauma_cur_path_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text(loc.get_string("label-valid-path"), color=(100, 150, 250))
                dpg.add_text(
                    loc.get_string("label-not-defined"),
                    tag="barotrauma_cur_path_valid",
                    color=(255, 0, 0),
                )

            dpg.add_separator()

            dpg.add_button(
                label=loc.get_string("base-close"),
                tag="baro_window_close_bth",
                callback=lambda: dpg.delete_item("baro_window"),
            )

            if AppConfig.get("experimental", False):
                dpg.add_button(
                    label=loc.get_string("btn-experimental-search-game-fold"),
                    callback=BarotraumaWindow._exp_game,
                )

            AppInterface.resize_windows()

    @staticmethod
    def validate_barotrauma_path(sender, app_data, user_data):
        from .mod_window import ModWindow

        dpg.disable_item("baro_window_close_bth")
        path = None
        try:
            path = Path(app_data)

            if path.exists() and (path / "config_player.xml").exists():
                dpg.set_value("barotrauma_cur_path_valid", "True")
                dpg.configure_item("barotrauma_cur_path_valid", color=[0, 255, 0])

                AppConfig.set("barotrauma_dir", str(path))
                AppConfig.get_mods_path()
                logger.info(f"Valid path set: {path}")

                ModManager.load_mods()
                ModManager.load_cslua_config()
                ModWindow.render_mods()
                return
            else:
                logger.warning(f"Invalid path or missing 'config_player.xml': {path}")

        except Exception as e:
            logger.error(f"Path validation error: {e}", exc_info=True)

        finally:
            if path is None:
                path = AppConfig.get("barotrauma_dir", loc.get_string("base-not-set"))

            has_cs = AppConfig.get("has_cs")
            has_lua = AppConfig.get("has_lua")

            dpg.set_value(
                "cs_scripting_status",
                loc.get_string("base-yes") if has_cs else loc.get_string("base-no"),
            )
            dpg.configure_item(
                "cs_scripting_status",
                color=[0, 255, 0] if has_cs else [255, 0, 0],
            )

            dpg.set_value(
                "lua_status",
                loc.get_string("base-yes") if has_lua else loc.get_string("base-no"),
            )
            dpg.configure_item(
                "lua_status", color=[0, 255, 0] if has_lua else [255, 0, 0]
            )

            dpg.set_value("barotrauma_cur_path_text", path)
            dpg.set_value("directory_status_text", path)

            logging.debug(f"Path set for display: {path}")

            dpg.enable_item("baro_window_close_bth")

        dpg.set_value("barotrauma_cur_path_valid", "False")
        dpg.configure_item("barotrauma_cur_path_valid", color=[255, 0, 0])
        logger.error("Path validation failed and marked as invalid.")

    @staticmethod
    def _exp_game():
        from .app_interface import AppInterface

        with dpg.window(
            modal=True,
            tag="exp_game",
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_title_bar=True,
        ):
            dpg.add_text(
                loc.get_string("warning-exp-game-1"), color=(255, 100, 100), wrap=0
            )
            dpg.add_text(loc.get_string("warning-exp-game-2"), wrap=0)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label=loc.get_string("base-start"),
                    callback=lambda s, a: BarotraumaWindow.start_sek(),
                )

                dpg.add_button(
                    label=loc.get_string("base-close"),
                    callback=lambda s, a: dpg.delete_item("exp_game"),
                )

        AppInterface.resize_windows()

    @staticmethod
    def start_sek():
        threading.Thread(target=BarotraumaWindow._run_search, daemon=True).start()

    @staticmethod
    def _run_search():
        dpg.delete_item("exp_game", children_only=True)
        dpg.add_text(
            loc.get_string("search-exp-game"),
            parent="exp_game",
            wrap=400,
            color=(150, 150, 150),
        )
        dpg.add_loading_indicator(style=2, parent="exp_game")

        results = Game.search_all_games_on_all_drives()
        dpg.delete_item("exp_game", children_only=True)

        if results:
            dpg.add_text(
                loc.get_string("search-exp-game-done"), parent="exp_game", wrap=0
            )
            dpg.add_separator(parent="exp_game")
            for path in results:
                dpg.add_button(
                    label=str(path),
                    parent="exp_game",
                    user_data=path,
                    callback=BarotraumaWindow._select_and_close,
                )
        else:
            dpg.add_text(
                loc.get_string("search-exp-game-none"), parent="exp_game", wrap=0
            )
            dpg.add_separator(parent="exp_game")
            dpg.add_button(
                label=loc.get_string("base-close"),
                callback=lambda s, a: dpg.delete_item("exp_game"),
                parent="exp_game",
            )

    @staticmethod
    def _select_and_close(sender, app_data, user_data):
        dpg.set_value("barotrauma_input_path", str(user_data))
        threading.Thread(
            target=BarotraumaWindow.validate_barotrauma_path,
            args=(None, str(user_data), None),
            daemon=True,
        ).start()
        dpg.delete_item("exp_game")
