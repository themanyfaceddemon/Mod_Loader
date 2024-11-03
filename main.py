import argparse
import logging
from pathlib import Path

from colorama import Fore, Style, init

from Code.app import App
from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc
from Code.package import ModLoader


class FixedWidthFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname.strip(), "")
        record.levelname = f"{color}{record.levelname:<7}{Style.RESET_ALL}"
        return super().format(record)


def init_classes() -> None:
    AppGlobalsAndConfig.init()
    # ModLoader.init()


def main() -> None:
    logging.debug("Starting initialization of classes...")
    init_classes()
    logging.debug("Initialization complete. Loading translations...")

    loc.load_translations(
        Path(
            AppGlobalsAndConfig.get_data_root()
            / "localization"
            / AppGlobalsAndConfig.get("lang", "eng")  # type: ignore
        )
    )
    logging.debug("Translations loaded. Starting app...")

    App()
    logging.debug("App instance created. Running app...")
    App.run()
    logging.debug("App run completed.")


if __name__ == "__main__":
    init(autoreset=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Debug on")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    handler = logging.StreamHandler()
    formatter = FixedWidthFormatter(
        "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"
    )

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    main()
