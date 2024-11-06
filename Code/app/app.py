import logging

import dearpygui.dearpygui as dpg

from .app_initializer import AppInitializer


class App:
    def __init__(self) -> None:
        AppInitializer.initialize()

    @staticmethod
    def run() -> None:
        try:
            dpg.start_dearpygui()

        except Exception as e:
            logging.error(f"Error during running GUI: {e}")

        finally:
            logging.debug("Destroying app...")
            App.stop()  # DEBUG This line should help solve https://github.com/themanyfaceddemon/Mod_Loader/issues/13. While I'm watching. Cain
            dpg.destroy_context()

    @staticmethod
    def stop() -> None:
        dpg.stop_dearpygui()
