import logging
from pathlib import Path

import dearpygui.dearpygui as dpg

from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
from Code.package import ModLoader

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
            dpg.add_text("Barotrauma Path Settings", color=(200, 200, 250))

            dpg.add_input_text(
                hint="Enter Barotrauma Path",
                callback=BarotraumaWindow.validate_barotrauma_path,
                tag="barotrauma_input_path",
                width=300,
            )

            with dpg.group(horizontal=True):
                dpg.add_text("Current Path:", color=(100, 150, 250))
                dpg.add_text(
                    AppGlobalsAndConfig.get("barotrauma_dir", "Not Set"),  # type: ignore
                    tag="barotrauma_cur_path_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Valid Path:", color=(100, 150, 250))
                dpg.add_text(
                    "Not Defined", tag="barotrauma_cur_path_valid", color=(255, 0, 0)
                )

            dpg.add_separator()

            dpg.add_button(
                label=loc.get_string("base-close"),
                callback=lambda: dpg.delete_item("baro_window"),
                
            )

            if AppGlobalsAndConfig.get("experimental", False):
                dpg.add_button(
                    label=loc.get_string("btn-experimental-search-game-fold")
                )

            AppInterface.resize_windows()

    @staticmethod
    def validate_barotrauma_path(sender, app_data, user_data):
        from .mod_window import ModWindow

        path = None
        try:
            path = Path(app_data)

            if path.exists() and (path / "config_player.xml").exists():
                dpg.set_value("barotrauma_cur_path_valid", "True")
                dpg.configure_item("barotrauma_cur_path_valid", color=[0, 255, 0])

                AppGlobalsAndConfig.set("barotrauma_dir", str(path))

                logger.info(f"Valid path set: {path}")

                ModLoader.load()
                ModWindow.render_mods()
                return
            else:
                logger.warning(f"Invalid path or missing 'config_player.xml': {path}")

        except Exception as e:
            logger.error(f"Path validation error: {e}", exc_info=True)

        finally:
            if not path:
                path = AppGlobalsAndConfig.get(
                    "barotrauma_dir", loc.get_string("base-not-set")
                )

            enable_cs_scripting = AppGlobalsAndConfig.get("enable_cs_scripting")
            has_lua = AppGlobalsAndConfig.get("has_lua")

            dpg.set_value(
                "cs_scripting_status",
                loc.get_string("base-yes")
                if enable_cs_scripting
                else loc.get_string("base-no"),
            )
            dpg.configure_item(
                "cs_scripting_status",
                color=[0, 255, 0] if enable_cs_scripting else [255, 0, 0],
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

        dpg.set_value("barotrauma_cur_path_valid", "False")
        dpg.configure_item("barotrauma_cur_path_valid", color=[255, 0, 0])
        logger.error("Path validation failed and marked as invalid.")
