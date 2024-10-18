import dearpygui.dearpygui as dpg


def center_window(tag):
    if not dpg.does_item_exist(tag):
        return

    window_width = dpg.get_item_width(tag)
    window_height = dpg.get_item_height(tag)

    if window_height is None or window_width is None:
        return

    vp_width = dpg.get_viewport_client_width()
    vp_height = dpg.get_viewport_client_height()

    x_pos = (vp_width - window_width) // 2
    y_pos = (vp_height - window_height) // 2

    dpg.set_item_pos(tag, [x_pos, y_pos])
