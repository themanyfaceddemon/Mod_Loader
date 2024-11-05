import logging
import os
import platform
import subprocess

import dearpygui.dearpygui as dpg
import requests

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
from Code.package import ModLoader

from .barotrauma_window import BarotraumaWindow
from .mod_window import ModWindow


class AppInterface:
    @staticmethod
    def initialize():
        AppInterface._create_viewport_menu_bar()
        ModWindow.create_window()
        dpg.set_viewport_resize_callback(AppInterface.resize_windows)
        AppInterface.resize_windows()

    @staticmethod
    def _create_viewport_menu_bar():
        dpg.add_viewport_menu_bar(tag="main_view_bar")

        with dpg.menu(
            label=loc.get_string("menu-bar-settings-lable"), parent="main_view_bar"
        ):
            dpg.add_button(
                label=loc.get_string("btn-set-game-dir"),
                callback=BarotraumaWindow.create_window,
            )
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text(loc.get_string("btn-set-game-dir-desc"))

            dpg.add_checkbox(
                label=loc.get_string("setting-toggle-install-lua"),
                tag="settings_install_lua",
                default_value=AppGlobalsAndConfig.get("game_config_auto_lua", False),  # type: ignore
                callback=lambda s, a: AppGlobalsAndConfig.set(
                    "game_config_auto_lua", a
                ),
            )

            dpg.add_checkbox(
                label=loc.get_string("setting-toggle-skip-intro"),
                tag="settings_skip_intro",
                default_value=AppGlobalsAndConfig.get("game_config_skip_intro", False),  # type: ignore
                callback=lambda s, a: AppGlobalsAndConfig.set(
                    "game_config_skip_intro", a
                ),
            )

            dpg.add_checkbox(
                label=loc.get_string("menu-toggle-experimental"),
                default_value=AppGlobalsAndConfig.get("experimental", False),  # type: ignore
                callback=lambda s, a: AppGlobalsAndConfig.set("experimental", a),
            )

            dpg.add_combo(
                items=["eng", "rus"],
                label=loc.get_string("menu-language"),
                default_value=AppGlobalsAndConfig.get("lang", "eng"),  # type: ignore
                callback=lambda s, a: AppGlobalsAndConfig.set("lang", a),
                width=50,
            )

        dpg.add_menu_item(
            label=loc.get_string("menu-bar-start-game"),
            parent="main_view_bar",
            callback=AppInterface.start_game,
        )

    @staticmethod
    def resize_windows():
        viewport_width = dpg.get_viewport_width() - 40
        viewport_height = dpg.get_viewport_height() - 80

        windows = ["mod_window", "baro_window", "exp_game", "game_config_window"]
        for window in windows:
            if dpg.does_item_exist(window):
                dpg.configure_item(window, width=viewport_width, height=viewport_height)
                dpg_tools.center_window(window)

    @staticmethod
    def start_game():
        ModLoader.save_mods()

        game_dir = AppGlobalsAndConfig.get("barotrauma_dir", None)
        if not game_dir:
            AppInterface.show_error(loc.get_string("error-game-dir-not-set"))
            return

        skip_intro = AppGlobalsAndConfig.get("game_config_skip_intro", False)
        auto_install_lua = AppGlobalsAndConfig.get("game_config_auto_lua", False)

        if auto_install_lua:
            if AppInterface.download_and_run_updater(game_dir):
                AppInterface.run_game(skip_intro, game_dir)
            else:
                AppInterface.show_error("Failed to download or run the updater.")
        else:
            AppInterface.run_game(skip_intro, game_dir)

    @staticmethod
    def show_error(message):
        with dpg.window(label="Error"):
            dpg.add_text(message)

    @staticmethod
    def download_and_run_updater(game_dir):
        system = platform.system()
        urls = {
            "Windows": "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.win-x64.exe",
            "Darwin": "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.osx-x64",
            "Linux": "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.linux-x64",
        }

        file_name = {
            "Windows": "Luatrauma.AutoUpdater.win-x64.exe",
            "Darwin": "Luatrauma.AutoUpdater.osx-x64",
            "Linux": "Luatrauma.AutoUpdater.linux-x64",
        }

        if system not in urls:
            AppInterface.show_error(loc.get_string("error-unknown-os"))
            return False

        updater_path = os.path.join(game_dir, file_name[system])

        try:
            response = requests.get(urls[system], stream=True)
            response.raise_for_status()

            with open(updater_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            if system in ["Darwin", "Linux"]:
                subprocess.run(["chmod", "+x", updater_path], check=True)

            result = subprocess.run([updater_path], cwd=game_dir)

            return result.returncode == 0

        except Exception as e:
            logging.error(f"Error downloading or running updater: {e}")
            return False

    @staticmethod
    def run_game(skip_intro, game_dir):
        run_executable = {
            "Windows": "Barotrauma.exe",
            "Darwin": "Barotrauma.app/Contents/MacOS/Barotrauma",
            "Linux": "Barotrauma",
        }

        system = platform.system()
        if system not in run_executable:
            AppInterface.show_error(loc.get_string("error-unknown-os"))
            return

        executable_path = os.path.join(game_dir, run_executable[system])
        if not os.path.isfile(executable_path):
            AppInterface.show_error(f"Executable not found: {executable_path}")
            return

        parms = ["-skipintro"] if skip_intro else []

        try:
            subprocess.run([executable_path] + parms, cwd=game_dir)

        except Exception as e:
            logging.error(f"Error running the game: {e}")
            AppInterface.show_error(f"Error running the game: {e}")
