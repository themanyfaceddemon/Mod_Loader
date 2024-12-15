import gc
import logging
import threading

import dearpygui.dearpygui as dpg


class App:
    @staticmethod
    def run() -> None:
        try:
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
