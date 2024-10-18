import dearpygui.dearpygui as dpg
import dearpygui_extend as dpge
from dearpygui_async import DearPyGuiAsync

from Code.app_vars import AppGlobalsAndConfig
from Code.dpg_tools import center_window
from Code.loc import Localization as loc
from Code.package.loader import PackageLoader

from .fonts_setup import FontManager


class App:
    _dpg_async = DearPyGuiAsync()

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
        dpg.add_handler_registry(tag="main_registry")

        App.create_fd_window()
        App.create_main_window()
        dpg.set_viewport_resize_callback(App.set_up_main_window)

    @classmethod
    def run(cls) -> None:
        cls._dpg_async.run()

        dpg.destroy_context()

    @classmethod
    def stop(cls) -> None:
        dpg.stop_dearpygui()

    @staticmethod
    def file_browser_callback(sender, file, cancel_pressed):
        if not cancel_pressed:
            PackageLoader.load(file[0])
            for obj in PackageLoader._active_package:
                dpg.add_text(str(obj), parent="package_cw")

        if AppGlobalsAndConfig.get_config(
            "mod_package_path"
        ) and AppGlobalsAndConfig.get_config("player_config_path"):
            dpg.delete_item("warning_text")

        dpg.hide_item("fd_window")

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
            if not AppGlobalsAndConfig.get_config(
                "mod_package_path"
            ) or not AppGlobalsAndConfig.get_config("player_config_path"):
                dpg.add_text(
                    "config_player.xml not set!",
                    color=[255, 0, 0, 255],
                    tag="warning_text",
                )

            dpg.add_text("ffff")  # TODO loc
            dpg.add_button(
                label="set-player-config",
                callback=lambda: dpg.show_item("fd_window"),  # TODO loc
            )
            dpg.add_child_window(tag="package_cw")

    @classmethod
    def create_fd_window(cls):
        with dpg.window(
            label="Select config_player.xml",  # TODO loc
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
                filetype_filter=[
                    {"label": "XML Files", "formats": ["xml"]}
                ],  # TODO loc
                callback=App.file_browser_callback,
            )
