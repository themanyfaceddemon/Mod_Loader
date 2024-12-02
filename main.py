import argparse
import logging
import os
import platform
import sys
from tkinter import Tk, messagebox
from traceback import TracebackException
from typing import Any, Type

from colorama import Fore, Style, init

from Code.app import App
from Code.app_vars import AppConfig
from Code.game import Game
from Code.handlers import HashManager, ModManager
from Code.loc import Localization as loc


def show_error_message(title, message):
    root = Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<7}{Style.RESET_ALL}"
        return super().format(record)


def configure_logging(debug: bool):
    log_level = logging.DEBUG if debug else logging.INFO

    log_format = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"

    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(log_format)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(level=log_level, handlers=[console_handler], encoding="utf-8")


def initialize_components(debug: bool, *components: Type[Any]) -> None:
    for component in components:
        logging.debug(f"Initializing {component.__name__}...")
        init_method = getattr(component, "init", None)
        if callable(init_method):
            init_method(
                debug
            ) if "debug" in init_method.__code__.co_varnames else init_method()
            logging.debug(f"{component.__name__} initialized successfully.")

        else:
            raise AttributeError(
                f"{component.__name__} does not have a callable 'init' method."
            )


def args_no_gui(
    start_game: bool,
    auto_game_path: bool,
    auto_lua: bool,
    skip_intro: bool,
    process_btm: bool,
):
    if auto_game_path:
        game_path = AppConfig.get_game_path()
        if game_path is None:
            res = Game.search_all_games_on_all_drives()
            if res:
                AppConfig.set("barotrauma_dir", str(res[0]))
                AppConfig.set_steam_mods_path()
                ModManager.load_mods()
                ModManager.load_cslua_config()

            else:
                logging.error("Failed to set game path")
                return

    if auto_lua:
        Game.download_update_lua()

    if process_btm:
        ModManager.save_mods()

    if start_game:
        Game.run_game(skip_intro=skip_intro)


def main(debug: bool) -> None:
    logging.debug("Starting program...")
    initialize_components(debug, AppConfig, HashManager, loc, ModManager)
    logging.debug("Initialization complete. Program is ready to run.")

    app_instance = App()
    logging.debug("App instance created. Running app...")
    app_instance.run()
    logging.debug("App run completed.")


if __name__ == "__main__":
    try:
        init(autoreset=True)

        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument(
            "--ngui",
            action="store_true",
            help="Disables GUI startup, required to run other flags",
        )
        parser.add_argument(
            "--sg", action="store_true", help="Automatically launch the game"
        )
        parser.add_argument(
            "--apath",
            action="store_true",
            help="Automatically set the path if it does not exist",
        )
        parser.add_argument(
            "--alua", action="store_true", help="Automatic update / installation of lua"
        )
        parser.add_argument(
            "--si", action="store_true", help="Skip intro. Doesn't work without --sg"
        )
        parser.add_argument(
            "--pbmt",
            action="store_true",
            help="Enables processing of modifications to accept the work of disabled modules",
        )
        args = parser.parse_args()

        configure_logging(args.debug)

        platform_name = platform.system()
        if platform_name == "win32":
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["PYTHONUTF8"] = "1"

        elif platform_name == "Darwin":
            logging.warning(
                "ModLoader may have bugs on MacOS. Please report any issues to https://github.com/themanyfaceddemon/Mod_Loader/issues"
            )
        del platform_name

        if args.ngui:
            args_no_gui(args.sg, args.apath, args.alua, args.si, args.pbmt)

        else:
            main(args.debug)

    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback_exception = TracebackException(exc_type, exc_value, exc_tb)  # type: ignore
        error_message = "".join(traceback_exception.format())
        show_error_message("Error Message", error_message)
        input("Press Enter to exit...")
