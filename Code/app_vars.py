import atexit
import json
import logging
import platform
from pathlib import Path
from typing import Any, Dict, Optional


class AppConfig:
    user_config: Dict[str, Any] = {}

    _root: Path = Path(__file__).parents[1]
    _data_root: Path = _root / "Data"
    _user_config_path: Path = Path()

    @classmethod
    def init(cls, debug=False) -> None:
        if platform.system() == "Windows":
            AppConfig._user_config_path = (
                Path.home()
                / "AppData"
                / "Roaming"
                / "BarotraumaModdingTool"
                / "config.json"
            )
        elif platform.system() == "Linux":
            AppConfig._user_config_path = (
                Path.home() / ".config" / "BarotraumaModdingTool" / "config.json"
            )
        elif platform.system() == "Darwin":
            AppConfig._user_config_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "BarotraumaModdingTool"
                / "config.json"
            )

        cls._load_user_config()
        cls.set("debug", debug)
        atexit.register(cls._save_user_config)

    @classmethod
    def _load_user_config(cls) -> None:
        if cls._user_config_path.exists():
            try:
                with open(cls._user_config_path, "r", encoding="utf-8") as file:
                    cls.user_config = json.load(file)

            except json.JSONDecodeError as err:
                logging.error(f"Error while decoding user_config.json: {err}")

    @classmethod
    def _save_user_config(cls) -> None:
        cls.user_config.pop("debug")

        cls._user_config_path.mkdir(parents=True, exist_ok=True)

        with open(cls._user_config_path, "w", encoding="utf-8") as file:
            json.dump(cls.user_config, file, indent=4, sort_keys=True)

    @classmethod
    def get_data_root(cls) -> Path:
        return cls._data_root

    @classmethod
    def get(cls, key: str, default=None) -> Optional[Any]:
        return cls.user_config.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls.user_config[key] = value
