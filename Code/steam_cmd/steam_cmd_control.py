import logging
import subprocess
from .steam_cmd_installer import SteamCMDInstaller
from Code.app_vars import AppConfig

logger = logging.getLogger(__name__)


class SteamCMDControl:
    _GAME_ID: int = 602960

    @classmethod
    def init(cls):
        SteamCMDInstaller.install()

    @classmethod
    def download_item(cls, item_id: int):
        anon_download_mod = AppConfig.get("anonymous_download_mod", True)
        if anon_download_mod is not True:
            return ""

        command = f"workshop_download_item {cls._GAME_ID} {item_id} +quit"

        try:
            subprocess.run([str(AppConfig.get_steam_cmd_exec()), command], check=True)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running SteamCMD: {e}")

        return (
            AppConfig.get_steam_cmd_path()
            / "steamapps/workshop/content"
            / str(cls._GAME_ID)
            / str(item_id)
        )
