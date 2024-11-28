import logging
import platform
import subprocess
from typing import List

import requests
from Code.app_vars import AppConfig

logger = logging.getLogger("GameProcessor")


class Game:
    _EXECUTABLES = {
        "Windows": "Barotrauma.exe",
        "Darwin": "Barotrauma.app/Contents/MacOS/Barotrauma",
        "Linux": "Barotrauma",
    }

    _LUA = {
        "Windows": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.win-x64.exe",
            "Luatrauma.AutoUpdater.win-x64.exe",
        ),
        "Darwin": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.osx-x64",
            "Luatrauma.AutoUpdater.osx-x64",
        ),
        "Linux": (
            "https://github.com/Luatrauma/Luatrauma.AutoUpdater/releases/download/latest/Luatrauma.AutoUpdater.linux-x64",
            "Luatrauma.AutoUpdater.linux-x64",
        ),
    }

    @staticmethod
    def run_game(install_lua: bool = False, skip_intro: bool = False):
        if install_lua:
            Game._download_update_lua()

        parms = ["-skipintro"] if skip_intro else []
        Game._run_exec(parms)

    @staticmethod
    def _download_update_lua():
        lua = Game._LUA.get(platform.system(), None)
        if not lua:
            raise RuntimeError("Unknown operating system")

        game_path = AppConfig.get_game_path()
        if game_path is None:
            return

        url = lua[0]
        exec_file = lua[1]

        updater_path = game_path / exec_file

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # total_size = int(response.headers.get("Content-Length", 0))
            downloaded_size = 0
            chunk_size = 4092
            with open(updater_path, "wb") as file:
                for i, chunk in enumerate(response.iter_content(chunk_size=chunk_size)):
                    file.write(chunk)
                    downloaded_size += len(chunk)  # TODO: Loading bar

            if platform.system() in ["Darwin", "Linux"]:
                subprocess.run(["chmod", "+x", str(updater_path)], check=True)

            result = subprocess.run([str(updater_path)], cwd=str(game_path))

            return result.returncode == 0

        except requests.RequestException as e:
            logger.error(f"Network error while downloading updater: {e}")
            return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting execute permissions: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error during download or execution: {e}")
            return False

    @staticmethod
    def _run_exec(parms: List[str] = []):
        try:
            exec_file = Game._EXECUTABLES.get(platform.system())
            if exec_file is None:
                raise RuntimeError("Unknown operating system")

            game_path = AppConfig.get_game_path()
            if game_path is None:
                return

            executable_path = game_path / exec_file
            if not executable_path.exists():
                logger.error(f"Executable not found: {executable_path}")
                return

            subprocess.run([str(executable_path)] + parms, cwd=str(game_path))

        except Exception as e:
            logger.error(f"Error running the game: {e}")
