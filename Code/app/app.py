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
            logging.debug("Destroying context...")
            dpg.destroy_context()
            logging.debug("Context destroyed.")

    @staticmethod
    def stop() -> None:
        dpg.stop_dearpygui()
