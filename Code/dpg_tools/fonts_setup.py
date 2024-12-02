import dearpygui.dearpygui as dpg

from Code.app_vars import AppConfig


class FontManager:
    @staticmethod
    def load_fonts():
        font_base_path = AppConfig.get_root_path() / "fonts"

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

        dpg.bind_font(default_font)
