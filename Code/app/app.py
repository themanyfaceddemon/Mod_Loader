import gc
import logging
import threading

import dearpygui.dearpygui as dpg

from .app_initializer import AppInitializer


class App:
    def __init__(self) -> None:
        AppInitializer.initialize()

    @staticmethod
    def run() -> None:
        try:
            dpg.show_debug()
            dpg.show_metrics()
            dpg.start_dearpygui()

        except Exception as e:
            logging.error(f"Error during running GUI: {e}")

        finally:
            logging.debug("Destroying app...")
            gc.collect()

            for thread in threading.enumerate():
                logging.debug(
                    f"Thread Name: {thread.name}, Alive: {thread.is_alive()}, Daemon: {thread.daemon}"
                )

            dpg.destroy_context()

    @staticmethod
    def stop() -> None:
        dpg.stop_dearpygui()
