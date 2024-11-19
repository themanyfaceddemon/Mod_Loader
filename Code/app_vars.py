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
    _user_data_path: Path = Path()

    @classmethod
    def init(cls, debug=False) -> None:
        if platform.system() == "Windows":
            cls._user_data_path = (
                Path.home() / "AppData" / "Roaming" / "BarotraumaModdingTool"
            )
        
        elif platform.system() == "Linux":
            cls._user_data_path = Path.home() / ".config" / "BarotraumaModdingTool"
        
        elif platform.system() == "Darwin":
            cls._user_data_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "BarotraumaModdingTool"
            )
        
        else:
            raise RuntimeError("Unknown operating system")

        cls._user_data_path.mkdir(parents=True, exist_ok=True)
        cls._load_user_config()
        cls.set("debug", debug)
        atexit.register(cls._save_user_config)

    @classmethod
    def _load_user_config(cls) -> None:
        config_path = cls._user_data_path / "config.json"

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    cls.user_config = json.load(file)

            except json.JSONDecodeError as err:
                logging.error(f"Error while decoding user_config.json: {err}")

    @classmethod
    def _save_user_config(cls) -> None:
        config_path = cls._user_data_path / "config.json"
        cls.user_config.pop("debug")

        with open(config_path, "w", encoding="utf-8") as file:
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
