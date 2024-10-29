import logging
import sys
from pathlib import Path

import dearpygui.dearpygui as dpg
from dearpygui_async import DearPyGuiAsync

from Code.loc import Localization as loc
from Code.package import ModLoader, Package

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

    def _setup_viewport(self):
        dpg.create_viewport(
            title=loc.get_string("viewport-name"),
            width=600,
            min_width=600,
            height=400,
            min_height=400,
        )

    def create_windows(self):
        ModLoader.load_mods()
        ModLoader.sort()
        ModLoader.save_mods()
        return
        with dpg.window(label="Main Window", no_background=True):
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text("Active Mods")
                    with dpg.child_window(tag="active_mods_child", width=300):
                        for mod in ModLoader.active_mods:
                            dpg.add_text(mod.identifier.name, wrap=0)
                            dpg.add_text("---", color=[255, 0, 0, 255])

                with dpg.group():
                    dpg.add_text("Inactive Mods")
                    with dpg.child_window(tag="inactive_mods_child", width=300):
                        for mod in ModLoader.inactive_mods:
                            dpg.add_text(mod.identifier.name, wrap=0)
                            dpg.add_text("---", color=[255, 0, 0, 255])

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
        pass
