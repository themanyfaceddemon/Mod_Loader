import argparse
import logging
from pathlib import Path

from Code.app_vars import AppGlobalsAndConfig
from Code.gui.client_app import App
from Code.loc import Localization as loc


class FixedWidthFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{record.levelname:<7}"
        return super().format(record)


def init_classes() -> None:
    AppGlobalsAndConfig.init()


def main() -> None:
    init_classes()
    loc.load_translations(
        Path(
            AppGlobalsAndConfig.get_data_root()
            / "localization"
            / AppGlobalsAndConfig.get_config("lang", "eng")  # type: ignore
        )
    )

    App()
    App.run()


if __name__ == "__main__":
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
