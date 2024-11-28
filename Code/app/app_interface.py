import json
import logging

import dearpygui.dearpygui as dpg

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppConfig
from Code.game import Game
from Code.loc import Localization as loc
from Code.package import ModManager

from .barotrauma_window import BarotraumaWindow
from .mod_window import ModWindow

logger = logging.getLogger("App")


class AppInterface:
    @staticmethod
    def initialize():
        AppInterface._create_viewport_menu_bar()
        AppInterface._create_main_window()
        ModWindow.create_window()
        dpg.set_viewport_resize_callback(AppInterface.resize_windows)
        AppInterface.resize_windows()

    @staticmethod
    def _create_main_window():
        with dpg.window(
            no_move=True,
            no_resize=True,
            no_title_bar=True,
            tag="main_window",
        ):
            dpg.add_tab_bar(tag="main_tab_bar")

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
                default_value=AppConfig.get("game_config_auto_lua", False),  # type: ignore
                callback=lambda s, a: AppConfig.set("game_config_auto_lua", a),
            )

            dpg.add_checkbox(
                label=loc.get_string("setting-toggle-skip-intro"),
                tag="settings_skip_intro",
                default_value=AppConfig.get("game_config_skip_intro", False),  # type: ignore
                callback=lambda s, a: AppConfig.set("game_config_skip_intro", a),
            )

            dpg.add_checkbox(
                label=loc.get_string("menu-toggle-experimental"),
                default_value=AppConfig.get("experimental", False),  # type: ignore
                callback=lambda s, a: AppConfig.set("experimental", a),
            )

            lang_dict = {
                "eng": loc.get_string("lang_code-eng"),
                "rus": loc.get_string("lang_code-rus"),
                "ger": loc.get_string("lang_code-ger"),
            }

            dpg.add_combo(
                items=list(lang_dict.values()),
                label=loc.get_string("menu-language"),
                default_value=lang_dict[AppConfig.get("lang", "eng")],  # type: ignore
                callback=lambda s, a: AppConfig.set(
                    "lang", next(key for key, value in lang_dict.items() if value == a)
                ),
            )

        dpg.add_menu_item(
            label=loc.get_string("menu-bar-start-game"),
            parent="main_view_bar",
            callback=AppInterface.start_game,
        )

        dpg.add_menu_item(
            label=loc.get_string("cac-window-name"),
            parent="main_view_bar",
            callback=AppInterface.create_cac_window,
        )

    @staticmethod
    def resize_windows():
        viewport_width = dpg.get_viewport_width() - 40
        viewport_height = dpg.get_viewport_height() - 80

        windows = [
            "main_window",
            "baro_window",
            "exp_game",
            "game_config_window",
            "cac_window",
        ]
        for item in windows:
            if dpg.does_item_exist(item):
                dpg.configure_item(item, width=viewport_width, height=viewport_height)
                dpg_tools.center_window(item)

        half_item = [
            "active_mod_search_tag",
            "active_mods_child",
            "inactive_mod_search_tag",
            "inactive_mods_child",
        ]
        viewport_width = viewport_width / 2
        viewport_height = viewport_height / 2
        for item in half_item:
            if dpg.does_item_exist(item):
                dpg.configure_item(item, width=viewport_width, height=viewport_height)

    @staticmethod
    def start_game():
        ModManager.save_mods()

        game_dir = AppConfig.get("barotrauma_dir", None)
        if game_dir is None:
            AppInterface.show_error(loc.get_string("error-game-dir-not-set"))
            return

        skip_intro = AppConfig.get("game_config_skip_intro", False)
        auto_install_lua = AppConfig.get("game_config_auto_lua", False)
        try:
            Game.run_game(auto_install_lua, skip_intro)  # type: ignore

        except Exception as err:
            AppInterface.show_error(err)

    @staticmethod
    def show_error(message):
        with dpg.window(label="Error"):
            dpg.add_text(message)

    @staticmethod
    def create_cac_window():
        if dpg.does_item_exist("cac_window"):
            dpg.focus_item("cac_window")
            return

        contributors_path = AppConfig.get_data_root() / "contributors.json"

        try:
            with open(contributors_path, "r", encoding="utf-8") as f:
                contributors_data = json.load(f)

        except Exception as e:
            logger.error(f"{contributors_path} just fuck up: {e}")
            return

        category_config = {
            "сaс-devs": {
                "name_field": "name",
                "info_field": "role",
                "info_process": lambda val: loc.get_string(val),
            },
            "сaс-translators": {
                "name_field": "name",
                "info_field": "code",
                "info_process": lambda val: loc.get_string(
                    "cac-translators-thx", lang_code=loc.get_string(f"lang_code-{val}")
                ),
            },
            "cac-special-thanks": {
                "name_field": "to",
                "info_field": "desc",
                "info_process": lambda val: loc.get_string(val),
            },
        }

        with dpg.window(
            label=loc.get_string("cac-window-name"),
            tag="cac_window",
            no_collapse=True,
            no_move=True,
            no_resize=True,
        ):
            for category_label, contributors_list in contributors_data.items():
                with dpg.collapsing_header(
                    label=loc.get_string(category_label), default_open=True
                ):
                    if isinstance(contributors_list, list):
                        for contributor in contributors_list:
                            with dpg.group(horizontal=True):
                                config = category_config.get(category_label)
                                if config:
                                    name = contributor.get(
                                        config["name_field"],
                                        loc.get_string("base-unknown"),
                                    )
                                    info_val = contributor.get(config["info_field"], "")
                                    info_text = (
                                        config["info_process"](info_val)
                                        if info_val
                                        else ""
                                    )
                                    dpg.add_text(name, color=(0, 150, 255))
                                    if info_text:
                                        dpg.add_text(
                                            f"- {info_text}",
                                            color=(200, 200, 200),
                                            wrap=0,
                                        )

            AppInterface.resize_windows()
