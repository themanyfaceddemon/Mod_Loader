import logging
import sys

import dearpygui.dearpygui as dpg
from dearpygui_async import DearPyGuiAsync

import Code.dpg_tools as dpg_tools
from Code.loc import Localization as loc
from Code.package import ModLoader, Package

from .fonts_setup import FontManager


class App:
    _dpg_async = DearPyGuiAsync()
    _filter_text = ""
    dragged_mod_id = None

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
        ModLoader.process_conflicts()

        with dpg.window(
            no_move=True,
            no_resize=True,
            no_title_bar=True,
            tag="main_window",
        ):
            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text("Active Mods")
                    with dpg.child_window(
                        tag="active_mods_child",
                        width=300,
                        drop_callback=self.on_mod_dropped,
                        user_data="active",
                        payload_type="MOD_DRAG",
                    ):
                        for mod in ModLoader.active_mods:
                            self.add_movable_mod(mod, "active", "active_mods_child")

                with dpg.group():
                    dpg.add_text("Inactive Mods")
                    with dpg.child_window(
                        tag="inactive_mods_child",
                        width=300,
                        drop_callback=self.on_mod_dropped,
                        user_data="inactive",
                        payload_type="MOD_DRAG",
                    ):
                        for mod in ModLoader.inactive_mods:
                            self.add_movable_mod(mod, "inactive", "inactive_mods_child")

        dpg.set_viewport_resize_callback(lambda: App.resize_main_window())

    def render_mods(self):
        dpg.delete_item("active_mods_child", children_only=True)
        for mod in ModLoader.active_mods:
            self.add_movable_mod(mod, "active", "active_mods_child")

        dpg.delete_item("inactive_mods_child", children_only=True)
        for mod in ModLoader.inactive_mods:
            self.add_movable_mod(mod, "inactive", "inactive_mods_child")

    def add_movable_mod(self, mod: Package, status: str, parent):
        mod_group_tag = f"{mod.identifier.id}_{status}_group"

        with dpg.group(tag=mod_group_tag, parent=parent):
            mod_button = dpg.add_button(
                label=mod.identifier.name,
                drop_callback=self.on_mod_dropped,
                payload_type="MOD_DRAG",
                user_data={"mod_id": mod.identifier.id, "status": status},
            )

            with dpg.drag_payload(
                parent=mod_button,
                payload_type="MOD_DRAG",
                drag_data={"mod_id": mod.identifier.id, "status": status},
            ):
                dpg.add_text(mod.identifier.name)

            dpg.add_separator()

    def on_mod_dropped(self, sender, app_data, user_data):
        drag_data = app_data
        dragged_mod_id = drag_data["mod_id"]
        dragged_mod_status = drag_data["status"]

        sender_type = dpg.get_item_type(sender)

        if sender_type == "mvAppItemType::mvButton":
            target_mod_data = dpg.get_item_user_data(sender)
            target_mod_id = target_mod_data["mod_id"]  # type: ignore
            target_mod_status = target_mod_data["status"]  # type: ignore

            if dragged_mod_status != target_mod_status:
                if target_mod_status == "active":
                    ModLoader.activate_mod(dragged_mod_id)
                else:
                    ModLoader.deactivate_mod(dragged_mod_id)
                dragged_mod_status = target_mod_status

            if dragged_mod_status == "active":
                ModLoader.swap_active_mods(dragged_mod_id, target_mod_id)
            else:
                ModLoader.swap_inactive_mods(dragged_mod_id, target_mod_id)

        elif sender_type == "mvAppItemType::mvChildWindow":
            target_status = dpg.get_item_user_data(sender)
            if dragged_mod_status != target_status:
                if target_status == "active":
                    ModLoader.activate_mod(dragged_mod_id)
                else:
                    ModLoader.deactivate_mod(dragged_mod_id)
                dragged_mod_status = target_status

            if dragged_mod_status == "active":
                ModLoader.move_active_mod_to_end(dragged_mod_id)
            else:
                ModLoader.move_inactive_mod_to_end(dragged_mod_id)

        else:
            logging.warning(f"Unknown drop target: {sender}")

        self.render_mods()

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

    @staticmethod
    def resize_main_window():
        viewport_width = dpg.get_viewport_width() - 40
        viewport_height = dpg.get_viewport_height() - 80
        dpg.configure_item("main_window", width=viewport_width, height=viewport_height)
        dpg.configure_item("active_mods_child", width=(viewport_width / 2))
        dpg.configure_item("inactive_mods_child", width=(viewport_width / 2))
        dpg_tools.center_window("main_window")
