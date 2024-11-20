import sys

import dearpygui.dearpygui as dpg

from Code.app_vars import AppConfig


class FontManager:
    @staticmethod
    def load_fonts():
        font_base_path = AppConfig.get_data_root() / "fonts"

        with dpg.font_registry():
            with dpg.font(
                str(font_base_path / "Monocraft" / "Monocraft.otf"), 13
            ) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)

                dpg.add_font_range(0x0391, 0x03C9)  # Greek character range
                dpg.add_font_range(
                    0x2070, 0x209F
                )  # Range of upper and lower numerical indices

                if sys.platform == "win32":
                    _remap_chars()

        dpg.bind_font(default_font)


def _remap_chars():
    biglet = 0x0410
    for i1 in range(0x00C0, 0xE0):
        dpg.add_char_remap(i1, biglet)
        dpg.add_char_remap(i1 + 0x20, biglet + 0x20)
        biglet += 1

    dpg.add_char_remap(0x00A8, 0x0401)  # Ё
    dpg.add_char_remap(0x00B8, 0x0451)  # ё
