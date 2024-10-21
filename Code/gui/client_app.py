import logging
import sys

import dearpygui.dearpygui as dpg
import dearpygui_extend as dpge
from dearpygui_async import DearPyGuiAsync

from Code.app_vars import AppGlobalsAndConfig
from Code.dpg_tools import center_window, decode_string
from Code.loc import Localization as loc
from Code.package import PackageLoader, Package

from .fonts_setup import FontManager


class App:
    _dpg_async = DearPyGuiAsync()
    _filter_text = ""

    def __init__(self):
        self.initialize_app()
        self.create_windows()
        self.setup_menu_bar()

    def initialize_app(self):
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
        dpg.set_viewport_resize_callback(self.set_up_main_window)

    def create_windows(self):
        self.create_fd_window()
        self.create_main_window()

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

    def setup_menu_bar(self):
        with dpg.menu(parent="main_window_menu_bar", label=loc.get_string("menu-bar")):
            dpg.add_button(
                label=loc.get_string("set-barotrauma-dir"),
                callback=self.show_fd_window,
            )
            dpg.add_button(
                label=loc.get_string("toggle-viewport-fullscreen"),
                callback=lambda: dpg.toggle_viewport_fullscreen(),
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
        if not baro_dir:
            return

        PackageLoader.load(f"{baro_dir}/config_player.xml")
        App.refresh_mods_list()

    @staticmethod
    def refresh_mods_list():
        dpg.delete_item("package_cw", children_only=True)

        PackageLoader._active_packages.sort(
            key=lambda x: getattr(x, "order", float("inf"))
        )

        for obj in PackageLoader._active_packages:
            uuid = dpg.generate_uuid()
            dpg.add_text(
                obj.name,
                parent="package_cw",
                wrap=0,
                tag=uuid,
                drop_callback=App.reorder_mods_callback,
                payload_type="MOD_ORDER",
                user_data=obj,
            )
            dpg.add_drag_payload(
                label=obj.name, parent=uuid, payload_type="MOD_ORDER", drag_data=obj
            )
            App.create_package_tooltip(uuid, obj)
            dpg.add_separator(indent=40, parent="package_cw")

    @staticmethod
    def create_package_tooltip(parent_id, package_obj):
        with dpg.tooltip(parent=parent_id):
            App.add_package_info("use-lua-package", package_obj.has_lua)
            App.add_package_info("use-cs-package", package_obj.has_cs)
            App.add_package_info("use-dll-package", package_obj.has_dll)
            App.add_package_info("override-package", package_obj.override)

    @staticmethod
    def add_package_info(label_key, condition):
        with dpg.group(horizontal=True):
            dpg.add_text(loc.get_string(label_key))
            dpg.add_text(
                loc.get_string("yes") if condition else loc.get_string("no"),
                color=[255, 255, 0, 255] if condition else [255, 255, 255, 255],
            )

    def set_up_main_window(self):
        dpg.set_item_height("main_window", dpg.get_viewport_client_height())
        dpg.set_item_width("main_window", dpg.get_viewport_client_width())
        center_window("main_window")

    def create_main_window(self) -> None:
        with dpg.window(
            no_title_bar=True, no_move=True, no_resize=True, tag="main_window"
        ):
            dpg.add_menu_bar(tag="main_window_menu_bar")
            if not AppGlobalsAndConfig.get_config("barotrauma_dir_path"):
                dpg.add_text(
                    loc.get_string("user-not-set-barotrauma-dir"),
                    color=[255, 0, 0, 255],
                    tag="warning_text",
                    wrap=0,
                )
            dpg.add_input_text(
                callback=self.filter_items, hint=loc.get_string("filter-packs")
            )
            dpg.add_child_window(tag="package_cw")
            self.load_package()

    def create_fd_window(self):
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
                allow_multi_selection=False,
                allow_create_new_folder=False,
                show_ok_cancel=True,
                show_nav_icons=False,
                dirs_only=True,
                callback=self.file_browser_callback,
            )

    def filter_items(self, sender, app_data, user_data=None):
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

    @staticmethod
    def reorder_mods_callback(sender, drag_data):
        source_mod: Package = drag_data
        target_mod: Package = dpg.get_item_user_data(sender)  # type: ignore

        if source_mod.order != target_mod.order:
            source_order = source_mod.order
            target_order = target_mod.order

            if source_order < target_order:
                for mod in PackageLoader._active_packages:
                    if source_order < mod.order <= target_order:
                        mod.order -= 1
                source_mod.order = target_order
            else:
                for mod in PackageLoader._active_packages:
                    if target_order <= mod.order < source_order:
                        mod.order += 1
                source_mod.order = target_order

            App.refresh_mods_list()
