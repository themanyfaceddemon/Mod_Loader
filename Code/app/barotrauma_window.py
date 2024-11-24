import logging
import os
import platform
import string
import threading
from pathlib import Path

import dearpygui.dearpygui as dpg

from Code.app_vars import AppConfig
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
            if not path:
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

        results = BarotraumaWindow._search_all_games_on_all_drives()
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

    @staticmethod
    def _is_system_directory(path):
        if platform.system() == "Windows":
            system_dirs = [
                Path("C:\\Windows"),
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
            ]
            return path in system_dirs or path.is_relative_to(Path("C:\\Windows"))

        else:
            system_dirs = [
                Path("/usr"),
                Path("/etc"),
                Path("/bin"),
                Path("/sys"),
                Path("/sbin"),
                Path("/proc"),
                Path("/dev"),
                Path("/run"),
                Path("/tmp"),
                Path("/var"),
                Path("/boot"),
                Path("/lib"),
                Path("/lib64"),
                Path("/opt"),
                Path("/lost+found"),
                Path("/snap"),
                Path("/srv"),
            ]

            return path in system_dirs

    @staticmethod
    def _should_ignore_directory(entry, current_dir, game_name):
        ignored_directories = {
            "appdata",
            "temp",
            "cache",
            "logs",
            "backup",
            "bin",
            "obj",
            "history",
            "httpcache",
            "venv",
            "tmp",
            "programdata",
        }

        entry_name_lower = entry.name.lower()

        if entry_name_lower != ".steam" and (
            entry_name_lower.startswith((".", "_", "$", "~"))
            or entry_name_lower in ignored_directories
        ):
            logger.debug(f"Ignoring directory: {entry}")
            return True

        expected_structure = {
            ".steam": "steam",
            "steam": "steamapps",
            "steamapps": "common",
            "common": game_name.lower(),
        }

        expected_entry = expected_structure.get(current_dir.name.lower())
        if expected_entry and entry_name_lower != expected_entry:
            logger.debug(
                f"Ignoring directory: {entry} (in {current_dir.name}, not {expected_entry})"
            )
            return True

        return False

    @staticmethod
    def _search_all_games_on_all_drives():
        game_name = "barotrauma"

        if platform.system() == "Windows":
            drives = [
                Path(f"{drive}:\\")
                for drive in string.ascii_uppercase
                if Path(f"{drive}:\\").exists() and os.access(f"{drive}:\\", os.R_OK)
            ]

        else:
            drives = [
                Path(mount_point)
                for mount_point in Path("/mnt").glob("*")
                if mount_point.is_dir()
            ]

        logger.debug(f"Found drives: {len(drives)}")

        found_paths = []

        for drive in drives:
            logger.debug(f"Processing drive: {drive}")
            dirs_to_visit = [drive]

            while dirs_to_visit:
                current_dir = dirs_to_visit.pop()
                logger.debug(f"Processing directory: {current_dir}")

                if BarotraumaWindow._is_system_directory(current_dir):
                    logger.debug(f"Ignoring system folder: {current_dir}")
                    continue

                try:
                    for entry in current_dir.iterdir():
                        if entry.is_dir():
                            if BarotraumaWindow._should_ignore_directory(
                                entry, current_dir, game_name
                            ):
                                continue

                            if entry.name.lower() == game_name:
                                logger.debug(f"Match found: {entry}")
                                found_paths.append(entry)
                            else:
                                dirs_to_visit.append(entry)

                except PermissionError:
                    logger.debug(f"Access to directory {current_dir} denied")

                except Exception as e:
                    logger.debug(f"Error processing directory {current_dir}: {e}")

        executable_name = (
            "barotrauma.exe" if platform.system() == "Windows" else "barotrauma"
        )

        valid_paths = []
        for path in found_paths:
            for exec_file in path.rglob("[Bb]arotrauma*"):
                if exec_file.name.lower() == executable_name:
                    logger.debug(f"Verified executable in path: {exec_file}")
                    valid_paths.append(path)

        return valid_paths
