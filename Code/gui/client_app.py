import logging
import sys

import dearpygui.dearpygui as dpg
import dearpygui_extend as dpge
from dearpygui_async import DearPyGuiAsync

from Code.app_vars import AppGlobalsAndConfig
from Code.dpg_tools import center_window, decode_string
from Code.loc import Localization as loc
from Code.package import Package, PackageLoader

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
        self._setup_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()
        sys.excepthook = self.global_exception_handler
        dpg.set_viewport_resize_callback(self.set_up_main_window)

    def _setup_viewport(self):
        dpg.create_viewport(
            title=loc.get_string("viewport-name"),
            width=600,
            min_width=600,
            height=400,
            min_height=400,
        )

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
            self._add_menu_buttons()

    def _add_menu_buttons(self):
        dpg.add_button(
            label=loc.get_string("set-barotrauma-dir"),
            callback=self.show_fd_window,
        )
        dpg.add_button(
            label=loc.get_string("toggle-viewport-fullscreen"),
            callback=lambda: dpg.toggle_viewport_fullscreen(),
        )

    def show_fd_window(self):
        if dpg.is_item_shown("fd_window"):
            dpg.focus_item("fd_window")
        else:
            dpg.show_item("fd_window")

    def file_browser_callback(self, sender, file, cancel_pressed):
        if not cancel_pressed:
            AppGlobalsAndConfig.set_config("barotrauma_dir_path", file[0])
            dpg.delete_item("warning_text")
            self.load_package()

        dpg.hide_item("fd_window")

    def load_package(self) -> None:
        baro_dir = AppGlobalsAndConfig.get_config("barotrauma_dir_path")
        if not baro_dir:
            return

        PackageLoader.load(f"{baro_dir}/config_player.xml")
        self.refresh_mods_list()

    def refresh_mods_list(self):
        dpg.delete_item("package_cw", children_only=True)
        self._sort_packages()

        for obj in PackageLoader._active_packages:
            self._create_package_item(obj)

    def _sort_packages(self):
        PackageLoader._active_packages.sort(
            key=lambda x: getattr(x, "order", float("inf"))
        )

    def _create_package_item(self, obj):
        uuid = dpg.generate_uuid()
        dpg.add_text(
            obj.name,
            parent="package_cw",
            wrap=0,
            tag=uuid,
            drop_callback=self.reorder_mods_callback,
            payload_type="MOD_ORDER",
            user_data=obj,
        )
        dpg.add_drag_payload(
            label=obj.name, parent=uuid, payload_type="MOD_ORDER", drag_data=obj
        )
        self.create_package_tooltip(uuid, obj)
        dpg.add_separator(indent=40, parent="package_cw")

    def create_package_tooltip(self, parent_id, package_obj):
        with dpg.tooltip(parent=parent_id):
            self.add_package_info("use-lua-package", package_obj.has_lua)
            self.add_package_info("use-cs-package", package_obj.has_cs)
            self.add_package_info("use-dll-package", package_obj.has_dll)
            self.add_package_info("override-package", package_obj.override)

    def add_package_info(self, label_key, condition):
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
            self._add_main_window_content()

    def _add_main_window_content(self):
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
        self._filter_mods()

    def _filter_mods(self):
        children = dpg.get_item_children("package_cw", 1)
        if not children:
            return

        show_separator = False
        for item in children:
            item_type = dpg.get_item_type(item)
            if item_type == "mvAppItemType::mvText":
                show_separator = self._filter_item_by_text(item, show_separator)
            elif item_type == "mvAppItemType::mvSeparator":
                self._toggle_separator(item, show_separator)

    def _filter_item_by_text(self, item, show_separator):
        item_text = dpg.get_value(item)
        if not item_text or App._filter_text not in item_text.lower():
            dpg.hide_item(item)
            return show_separator
        dpg.show_item(item)
        return True

    def _toggle_separator(self, item, show_separator):
        if show_separator:
            dpg.show_item(item)
        else:
            dpg.hide_item(item)

    def reorder_mods_callback(self, sender, drag_data):
        source_mod: Package = drag_data
        target_mod: Package = dpg.get_item_user_data(sender)  # type: ignore

        if source_mod.order != target_mod.order:
            self._reorder_mods(source_mod, target_mod)
            self.refresh_mods_list()

    def _reorder_mods(self, source_mod, target_mod):
        source_order = source_mod.order
        target_order = target_mod.order

        if source_order < target_order:
            for mod in PackageLoader._active_packages:
                if source_order < mod.order <= target_order:
                    mod.order -= 1  # type: ignore
            source_mod.order = target_order
        else:
            for mod in PackageLoader._active_packages:
                if target_order <= mod.order < source_order:
                    mod.order += 1  # type: ignore
            source_mod.order = target_order
