import logging
import os
import subprocess
import sys
import dearpygui.dearpygui as dpg
from Code.package import ModLoader, Package
import Code.dpg_tools as dpg_tools
from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
import platform
from .barotrauma_window import BarotraumaWindow
from .mod_window import ModWindow


class AppInterface:
    @staticmethod
    def initialize():
        AppInterface._create_viewport_menu_bar()
        ModWindow.create_window()

        dpg.set_viewport_resize_callback(lambda: AppInterface.resize_windows())
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
                callback=AppInterface.enable_auto_install_lua,
            )

            dpg.add_checkbox(
                label=loc.get_string("setting-toggle-skip-intro"),
                tag="settings_skip_intro",
                default_value=AppGlobalsAndConfig.get("game_config_skip_intro", False),  # type: ignore
                callback=AppInterface.enable_auto_skip_intro,
            )

            dpg.add_checkbox(
                label=loc.get_string("menu-toggle-experimental"),
                callback=lambda s, a: AppGlobalsAndConfig.set("experimental", a),
                default_value=AppGlobalsAndConfig.get("experimental", False),  # type: ignore
            )
            dpg.add_combo(
                items=["eng", "rus"],
                label=loc.get_string("menu-language"),
                default_value=AppGlobalsAndConfig.get("lang", "eng"),  # type: ignore
                callback=lambda s, a: AppGlobalsAndConfig.set(
                    "lang", a
                ),  # TODO: Dynamic language replacement
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

        if dpg.does_item_exist("mod_window"):
            dpg.configure_item(
                "mod_window", width=viewport_width, height=viewport_height
            )
            dpg_tools.center_window("mod_window")

            dpg.configure_item("active_mods_child", width=(viewport_width / 2))
            dpg.configure_item("active_mod_search_tag", width=(viewport_width / 2))
            dpg.configure_item("inactive_mods_child", width=(viewport_width / 2))
            dpg.configure_item("inactive_mod_search_tag", width=(viewport_width / 2))

        if dpg.does_item_exist("baro_window"):
            dpg.configure_item(
                "baro_window", width=viewport_width, height=viewport_height
            )
            dpg_tools.center_window("baro_window")

        if dpg.does_item_exist("exp_game"):
            dpg.configure_item("exp_game", width=viewport_width, height=viewport_height)
            dpg_tools.center_window("exp_game")

        if dpg.does_item_exist("game_config_window"):
            dpg.configure_item(
                "game_config_window", width=viewport_width, height=viewport_height
            )
            dpg_tools.center_window("game_config_window")

    @staticmethod
    def enable_auto_install_lua(sender, app_data, user_data):
        if app_data:
            AppGlobalsAndConfig.set("game_config_auto_lua", True)
            AppGlobalsAndConfig.set("game_config_skip_intro", False)
            dpg.set_value("settings_skip_intro", False)
        else:
            AppGlobalsAndConfig.set("game_config_auto_lua", False)

    @staticmethod
    def enable_auto_skip_intro(sender, app_data, user_data):
        if app_data:
            AppGlobalsAndConfig.set("game_config_skip_intro", True)
            AppGlobalsAndConfig.set("game_config_auto_lua", False)
            dpg.set_value("settings_install_lua", False)
        else:
            AppGlobalsAndConfig.set("game_config_skip_intro", False)

    @staticmethod
    def start_game():
        ModLoader.save_mods()

        game_dir = AppGlobalsAndConfig.get("barotrauma_dir", None)
        if not game_dir:
            AppInterface.show_error("Game dir not set!")
            return

        skip_intro = AppGlobalsAndConfig.get("game_config_skip_intro", False)
        auto_install_lua = AppGlobalsAndConfig.get("game_config_auto_lua", False)

        if auto_install_lua:
            command = AppInterface.get_auto_install_command()
            if command:
                AppInterface.execute_command(command, game_dir)
        else:
            AppInterface.run_game(skip_intro, game_dir)

    @staticmethod
    def show_error(message):
        with dpg.window(label="error"):
            dpg.add_text(message)

    @staticmethod
    def get_auto_install_command():
        system = platform.system()
        if system == "Windows":
            return (
                'cmd /c "curl -L -z Luatrauma.AutoUpdater.win-x64.exe -o Luatrauma.AutoUpdater.win-x64.exe '
                "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.win-x64.exe && "
                'start /b Luatrauma.AutoUpdater.win-x64.exe"'
            )
        elif system == "Darwin":
            return (
                '/bin/zsh -c "cd Barotrauma.app/Contents/MacOS && '
                "/usr/bin/curl -L -O https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.osx-x64 && "
                'chmod +x Luatrauma.AutoUpdater.osx-x64 && ./Luatrauma.AutoUpdater.osx-x64"'
            )
        elif system == "Linux":
            return (
                'bash -c "wget https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.linux-x64 && '
                'chmod +x Luatrauma.AutoUpdater.linux-x64 && ./Luatrauma.AutoUpdater.linux-x64"'
            )
        else:
            AppInterface.show_error("Unknown operating system")
            return None

    @staticmethod
    def execute_command(command, cwd):
        try:
            subprocess.run(command, shell=True, cwd=cwd)
        except Exception as e:
            logging.error(f"Error executing command: {e}")

    @staticmethod
    def run_game(skip_intro, game_dir):
        parms = " -skipintro" if skip_intro else ""
        system = platform.system()

        if system == "Windows":
            run = "Barotrauma.exe"
        elif system == "Darwin":
            run = "Barotrauma.app"
        elif system == "Linux":
            run = "Barotrauma"
        else:
            AppInterface.show_error("Unknown operating system")
            return

        subprocess.run([sys.executable, f"{game_dir}/{run}{parms}"], cwd=game_dir)
