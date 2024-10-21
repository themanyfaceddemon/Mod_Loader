import logging
import sys

import dearpygui.dearpygui as dpg
import dearpygui_extend as dpge
from dearpygui_async import DearPyGuiAsync

from Code.app_vars import AppGlobalsAndConfig
from Code.dpg_tools import center_window, decode_string
from Code.loc import Localization as loc
from Code.package.loader import PackageLoader

from .fonts_setup import FontManager


class App:
    _dpg_async = DearPyGuiAsync()
    _filter_text = ""

    def __init__(self):
        dpg.create_context()
        FontManager.load_fonts()

        dpg.create_viewport(
            title=loc.get_string("viewport-name"),
            width=600,
            min_width=600,
            height=400,
            min_height=400,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        sys.excepthook = App.global_exception_handler
        dpg.add_handler_registry(tag="main_registry")

        App.create_fd_window()
        App.create_main_window()
        App.set_up_menu_bar_items()
        dpg.set_viewport_resize_callback(App.set_up_main_window)

    @classmethod
    def run(cls) -> None:
        cls._dpg_async.run()

        dpg.destroy_context()

    @classmethod
    def stop(cls) -> None:
        dpg.stop_dearpygui()

    @staticmethod
    def global_exception_handler(exctype, value, traceback_obj):
        logging.error("Exception occurred", exc_info=(exctype, value, traceback_obj))

    @staticmethod
    def set_up_menu_bar_items():
        with dpg.menu(parent="main_window_menu_bar", label=loc.get_string("menu-bar")):
            dpg.add_button(
                label=loc.get_string("set-player-config"),
                callback=App.show_fd_window,
            )

    @staticmethod
    def show_fd_window():
        if dpg.is_item_shown("fd_window"):
            dpg.focus_item("fd_window")

        else:
            dpg.show_item("fd_window")

    @staticmethod
    def file_browser_callback(sender, file, cancel_pressed):
        if not cancel_pressed:
            AppGlobalsAndConfig.set_config("barotrauma_dir_path", file[0])
            dpg.delete_item("warning_text")
            App.load_package()

        dpg.hide_item("fd_window")

    @staticmethod
    def load_package() -> None:
        baro_dir = AppGlobalsAndConfig.get_config("barotrauma_dir_path")

        if baro_dir:
            PackageLoader.load(baro_dir + "/config_player.xml")
            dpg.delete_item("package_cw", children_only=True)
            for obj in PackageLoader._active_packages:
                uuid = dpg.generate_uuid()
                dpg.add_text(obj.name, parent="package_cw", wrap=0, tag=uuid)
                with dpg.tooltip(parent=uuid):
                    with dpg.group(horizontal=True):
                        dpg.add_text(loc.get_string("use-lua-package"))
                        if obj.has_lua:
                            dpg.add_text(
                                loc.get_string("yes"), color=[255, 255, 0, 255]
                            )
                        else:
                            dpg.add_text(loc.get_string("no"))

                    with dpg.group(horizontal=True):
                        dpg.add_text(loc.get_string("use-cs-package"))
                        if obj.has_cs:
                            dpg.add_text(
                                loc.get_string("yes"), color=[255, 255, 0, 255]
                            )
                        else:
                            dpg.add_text(loc.get_string("no"))

                    with dpg.group(horizontal=True):
                        dpg.add_text(loc.get_string("use-dll-package"))
                        if obj.has_dll:
                            dpg.add_text(
                                loc.get_string("yes"), color=[255, 255, 0, 255]
                            )
                        else:
                            dpg.add_text(loc.get_string("no"))

                    with dpg.group(horizontal=True):
                        dpg.add_text(loc.get_string("override-package"))
                        if obj.override:
                            dpg.add_text(
                                loc.get_string("yes"), color=[255, 255, 0, 255]
                            )
                        else:
                            dpg.add_text(loc.get_string("no"))

                dpg.add_separator(indent=40, parent="package_cw")

    @classmethod
    def set_up_main_window(cls):
        dpg.set_item_height("main_window", dpg.get_viewport_client_height())
        dpg.set_item_width("main_window", dpg.get_viewport_client_width())
        center_window("main_window")

    @classmethod
    def create_main_window(cls) -> None:
        with dpg.window(
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            tag="main_window",
        ):
            dpg.add_menu_bar(tag="main_window_menu_bar")

            if not AppGlobalsAndConfig.get_config("barotrauma_dir_path"):
                dpg.add_text(
                    loc.get_string("user-not-set-barotrauma-dir"),
                    color=[255, 0, 0, 255],
                    tag="warning_text",
                )

            dpg.add_input_text(
                callback=App.filter_items, hint=loc.get_string("filter-packs")
            )

            dpg.add_child_window(tag="package_cw")
            App.load_package()

    @classmethod
    def create_fd_window(cls):
        with dpg.window(
            label=loc.get_string("fd-window-name"),
            tag="fd_window",
            show=False,
            no_close=True,
            no_collapse=True,
        ):
            dpge.add_file_browser(
                collapse_sequences=False,
                collapse_sequences_checkbox=False,
                path_input_style=0,
                add_filename_tooltip=False,
                tooltip_min_length=100,
                icon_size=1.0,
                allow_multi_selection=False,
                allow_drag=False,
                allow_create_new_folder=False,
                show_ok_cancel=True,
                show_nav_icons=False,
                dirs_only=True,
                callback=App.file_browser_callback,
            )

    @staticmethod
    def filter_items(sender, app_data, user_data=None):
        App._filter_text = decode_string(app_data).lower()

        children = dpg.get_item_children("package_cw", 1)
        if children is None:
            return

        show_separator = False
        for item in children:
            item_type = dpg.get_item_type(item)
            if item_type == "mvAppItemType::mvText":
                item_text = dpg.get_value(item)

                if item_text is None:
                    dpg.hide_item(item)
                    continue

                item_text = item_text.lower()

                if App._filter_text in item_text:
                    dpg.show_item(item)
                    show_separator = True
                else:
                    dpg.hide_item(item)

            elif item_type == "mvAppItemType::mvSeparator":
                if show_separator:
                    dpg.show_item(item)
                    show_separator = False

                else:
                    dpg.hide_item(item)
