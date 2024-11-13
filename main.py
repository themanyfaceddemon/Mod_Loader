import argparse
import logging
from pathlib import Path

from colorama import Fore, Style, init

from Code.app import App
from Code.app_vars import AppConfig
from Code.loc import Localization as loc
from Code.package import ModManager


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


def init_app_config(debug: bool) -> None:
    logging.debug("Initializing AppConfig...")
    AppConfig.init()
    AppConfig.set("debug", debug)
    logging.debug("AppConfig initialization complete.")


def load_mods() -> None:
    logging.debug("Loading mods...")
    ModManager.load_mods_and_configs()

    # ModManager.sort()
    logging.debug("Mods loaded successfully.")


def load_translations() -> None:
    logging.debug("Loading translations...")
    localization_path = (
        Path(AppConfig.get_data_root()) / "localization" / AppConfig.get("lang", "eng")  # type: ignore
    )
    loc.load_translations(localization_path)
    logging.debug("Translations loaded successfully.")


def init_classes(debug: bool) -> None:
    logging.debug("Starting application initialization...")
    init_app_config(debug)
    load_mods()
    load_translations()
    logging.debug("Application initialization complete.")


def main(debug: bool) -> None:
    logging.debug("Starting program...")
    init_classes(debug)
    logging.debug("Initialization complete. Program is ready to run.")

    return
    app_instance = App()
    logging.debug("App instance created. Running app...")
    app_instance.run()
    logging.debug("App run completed.")


if __name__ == "__main__":
    init(autoreset=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    configure_logging(args.debug)

    main(args.debug)
    logging.debug("I am dead")
