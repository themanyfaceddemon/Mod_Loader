import dearpygui.dearpygui as dpg

from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
from Code.package import ModLoader, Package

from .barotrauma_window import BarotraumaWindow


class ModWindow:
    dragged_mod_id = None
    active_mod_search_text = ""
    inactive_mod_search_text = ""

    @staticmethod
    def create_window():
        with dpg.window(
            no_move=True,
            no_resize=True,
            no_title_bar=True,
            tag="mod_window",
        ):
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label=loc.get_string("btn-sort-mods"),
                    callback=ModWindow.sort_active_mods,
                    tag="sort_button",
                )
                with dpg.tooltip("sort_button"):
                    dpg.add_text(loc.get_string("btn-sort-mods-desc"))

                dpg.add_button(
                    label=loc.get_string("btn-set-game-dir"),
                    callback=BarotraumaWindow.create_window,
                    tag="set_dir_button",
                )
                with dpg.tooltip("set_dir_button"):
                    dpg.add_text(loc.get_string("btn-set-game-dir-desc"))

            with dpg.group(horizontal=True):
                dpg.add_text("Directory Found:", color=(100, 150, 250))
                dpg.add_text(
                    str(
                        AppGlobalsAndConfig.get(
                            "barotrauma_dir", loc.get_string("base-not-set")
                        )
                    ),
                    tag="directory_status_text",
                    color=(200, 200, 250),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Enable CS Scripting:", color=(100, 150, 250))
                dpg.add_text(
                    loc.get_string("base-yes")
                    if AppGlobalsAndConfig.get("enable_cs_scripting")
                    else loc.get_string("base-no"),
                    tag="cs_scripting_status",
                    color=(0, 255, 0)
                    if AppGlobalsAndConfig.get("enable_cs_scripting")
                    else (255, 0, 0),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Lua Installed:", color=(100, 150, 250))
                dpg.add_text(
                    loc.get_string("base-yes")
                    if AppGlobalsAndConfig.get("has_lua")
                    else loc.get_string("base-no"),
                    tag="lua_status",
                    color=(0, 255, 0)
                    if AppGlobalsAndConfig.get("has_lua")
                    else (255, 0, 0),
                )

            with dpg.group(horizontal=True):
                dpg.add_text("nope =)", tag="error_count_text")
                dpg.add_text("|")
                dpg.add_text("nope =)", tag="warning_count_text")

            dpg.add_separator()

            with dpg.group(horizontal=True):
                with dpg.group():
                    dpg.add_text("Active Mods")
                    dpg.add_input_text(
                        tag="active_mod_search_tag",
                        hint="Search...",
                        callback=ModWindow.on_search_changed,
                        user_data="active",
                    )
                    with dpg.child_window(
                        tag="active_mods_child",
                        drop_callback=ModWindow.on_mod_dropped,
                        user_data="active",
                        payload_type="MOD_DRAG",
                    ):
                        pass

                with dpg.group():
                    dpg.add_text("Inactive Mods")
                    dpg.add_input_text(
                        tag="inactive_mod_search_tag",
                        hint="Search...",
                        callback=ModWindow.on_search_changed,
                        user_data="inactive",
                    )
                    with dpg.child_window(
                        tag="inactive_mods_child",
                        drop_callback=ModWindow.on_mod_dropped,
                        user_data="inactive",
                        payload_type="MOD_DRAG",
                    ):
                        pass

        ModWindow.render_mods()

    @staticmethod
    def on_search_changed(sender, app_data, user_data):
        if user_data == "active":
            ModWindow.active_mod_search_text = app_data.lower()

        elif user_data == "inactive":
            ModWindow.inactive_mod_search_text = app_data.lower()

        ModWindow.render_mods()

    @staticmethod
    def render_mods():
        ModLoader.process_errors()
        dpg.delete_item("active_mods_child", children_only=True)
        for mod in ModLoader.active_mods:
            if ModWindow.active_mod_search_text in mod.identifier.name.lower():
                ModWindow.add_movable_mod(mod, "active", "active_mods_child")

        dpg.delete_item("inactive_mods_child", children_only=True)
        for mod in ModLoader.inactive_mods:
            if ModWindow.inactive_mod_search_text in mod.identifier.name.lower():
                ModWindow.add_movable_mod(mod, "inactive", "inactive_mods_child")

        error_count, warning_count = ModWindow.count_mods_with_issues()
        dpg.set_value(
            "error_count_text", loc.get_string("error-count", count=error_count)
        )
        dpg.set_value(
            "warning_count_text", loc.get_string("warning-count", count=warning_count)
        )

    @staticmethod
    def add_movable_mod(mod: Package, status: str, parent):
        mod_group_tag = f"{mod.identifier.id}_{status}_group"
        mod_name_tag = f"{mod.identifier.id}_{status}_text"

        with dpg.group(tag=mod_group_tag, parent=parent):
            dpg.add_text(
                mod.identifier.name,
                tag=mod_name_tag,
                drop_callback=ModWindow.on_mod_dropped,
                payload_type="MOD_DRAG",
                user_data={"mod_id": mod.identifier.id, "status": status},
            )

            with dpg.popup(parent=mod_name_tag):
                with dpg.group(horizontal=True):
                    dpg.add_text("Author:", color=[0, 102, 204])
                    dpg.add_text(mod.metadata.meta.get("author", "Unknown"))

                with dpg.group(horizontal=True):
                    dpg.add_text("License:", color=[169, 169, 169])
                    dpg.add_text(
                        mod.metadata.meta.get("license", "Not specified"),
                        color=[169, 169, 169],
                    )

                with dpg.group(horizontal=True):
                    dpg.add_text("Game version:", color=[34, 139, 34])
                    dpg.add_text(mod.metadata.game_version)

                with dpg.group(horizontal=True):
                    dpg.add_text("Mod version:", color=[34, 139, 34])
                    dpg.add_text(mod.metadata.mod_version)

                if mod.metadata.errors:
                    dpg.add_text("Errors:", color=[255, 0, 0])
                    for error in mod.metadata.errors[:3]:
                        dpg.add_text(error, wrap=0, bullet=True)

                    if len(mod.metadata.errors) > 3:
                        dpg.add_text(
                            "See full details...", color=[255, 255, 0], bullet=True
                        )

                if mod.metadata.warnings:
                    dpg.add_text("Warnings:", color=[255, 255, 0])
                    for warning in mod.metadata.warnings[:3]:
                        dpg.add_text(warning, wrap=0, bullet=True)

                    if len(mod.metadata.warnings) > 3:
                        dpg.add_text(
                            "See full details...", color=[255, 255, 0], bullet=True
                        )

                dpg.add_button(
                    label="Show full details",
                    callback=lambda: ModWindow.show_details_window(mod),
                )

            with dpg.drag_payload(
                parent=mod_name_tag,
                payload_type="MOD_DRAG",
                drag_data={"mod_id": mod.identifier.id, "status": status},
            ):
                dpg.add_text(mod.identifier.name)

            if mod.metadata.errors:
                dpg.configure_item(mod_name_tag, color=[255, 0, 0])
            elif mod.metadata.warnings:
                dpg.configure_item(mod_name_tag, color=[255, 255, 0])
            else:
                dpg.configure_item(mod_name_tag, color=[255, 255, 255])

            dpg.add_separator()

    @staticmethod
    def show_details_window(mod: Package):
        title = f"MOD: {mod.identifier.name} - Full Details"
        window_tag = f"{mod.identifier.id}_full_details_window"

        if dpg.does_item_exist(window_tag):
            dpg.delete_item(window_tag)

        with dpg.window(
            label=title,
            width=400,
            height=300,
            tag=window_tag,
            on_close=lambda: dpg.delete_item(window_tag),
        ):
            with dpg.group(horizontal=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("Mod name:", color=[0, 102, 204])
                        dpg.add_text(mod.identifier.name)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Author:", color=[0, 102, 204])
                        dpg.add_text(mod.metadata.meta.get("author", "Unknown"))

                    with dpg.group(horizontal=True):
                        dpg.add_text("License:", color=[169, 169, 169])
                        dpg.add_text(
                            mod.metadata.meta.get("license", "Not specified"),
                            color=[169, 169, 169],
                        )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Is local mod:")
                        dpg.add_text("yes" if mod.metadata.local else "no")

                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("ModLoader ID:", color=[34, 139, 34])
                        dpg.add_text(mod.identifier.id)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Game version:", color=[34, 139, 34])
                        dpg.add_text(mod.metadata.game_version)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Mod version:", color=[34, 139, 34])
                        dpg.add_text(mod.metadata.mod_version)
            dpg.add_separator()

            if mod.metadata.errors:
                dpg.add_text("Errors:", color=[255, 0, 0])
                for error in mod.metadata.errors:
                    dpg.add_text(error, wrap=0, bullet=True)
                dpg.add_separator()

            if mod.metadata.warnings:
                dpg.add_text("Warnings:", color=[255, 255, 0])
                for warning in mod.metadata.warnings:
                    dpg.add_text(warning, wrap=0, bullet=True)
                dpg.add_separator()

    @staticmethod
    def on_mod_dropped(sender, app_data, user_data):
        drag_data = app_data
        dragged_mod_id = drag_data["mod_id"]
        dragged_mod_status = drag_data["status"]

        sender_type = dpg.get_item_type(sender)

        if sender_type == "mvAppItemType::mvText":
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

        ModWindow.render_mods()

    @staticmethod
    def sort_active_mods():
        ModLoader.sort()
        ModWindow.render_mods()

    @staticmethod
    def count_mods_with_issues():
        error_count = 0
        warning_count = 0

        for mod in ModLoader.active_mods:
            if mod.metadata.errors:
                error_count += 1

            if mod.metadata.warnings:
                warning_count += 1

        return error_count, warning_count