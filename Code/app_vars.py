import atexit
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class AppGlobalsAndConfig:
    user_config: Dict[str, Any] = {}

    _root: Path = Path(__file__).parents[1]
    _data_root: Path = _root / "Data"
    _user_config_path: Path = _data_root / "user_config.json"

    @classmethod
    def init(cls) -> None:
        cls._load_user_config()
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
