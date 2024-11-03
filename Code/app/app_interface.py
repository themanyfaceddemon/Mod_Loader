import dearpygui.dearpygui as dpg

import Code.dpg_tools as dpg_tools
from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc

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
                tag="set_dir_button",
            )
            with dpg.tooltip("set_dir_button"):
                dpg.add_text(loc.get_string("btn-set-game-dir-desc"))

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
