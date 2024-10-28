import logging
from pathlib import Path
import sys

import dearpygui.dearpygui as dpg
from dearpygui_async import DearPyGuiAsync

from Code.loc import Localization as loc
from Code.package import Package

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
        for path in Path(
            "G:\\Programs\\Steam\\steamapps\\workshop\\content\\602960"
        ).iterdir():  # DEBUG
            Package(path)

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
