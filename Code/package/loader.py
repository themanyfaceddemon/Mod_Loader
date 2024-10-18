import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from .package import Package
from Code.app_vars import AppGlobalsAndConfig


class PackageLoader:
    _active_package = []

    @staticmethod
    def _append_config(key: str, value: Any) -> None:
        if key not in AppGlobalsAndConfig.user_config:
            AppGlobalsAndConfig.user_config[key] = []

        AppGlobalsAndConfig.user_config[key].append(value)

    @staticmethod
    def load(file_path: str):
        PackageLoader._process_xml(file_path)
        PackageLoader._load_into_memory()

    @staticmethod
    def _load_into_memory():
        mod_package_path_active = AppGlobalsAndConfig.get_config(
            "mod_package_path_active"
        )
        if mod_package_path_active:
            for mod in mod_package_path_active:
                PackageLoader._active_package.append(
                    PackageLoader._pars_package(mod, False)
                )

        mod_package_path_local_active = AppGlobalsAndConfig.get_config(
            "mod_package_path_local_active"
        )
        if mod_package_path_local_active:
            for mod in mod_package_path_local_active:
                PackageLoader._active_package.append(
                    PackageLoader._pars_package(mod, True)
                )

    @staticmethod
    def _pars_package(package_path: str, local_load: bool) -> "Package":
        path = Path(package_path)
        path = path / "filelist.xml"
        if not path.exists():
            raise ValueError(f"Файл {path} не найден.")

        tree = ET.parse(str(path))
        root = tree.getroot()

        if root.tag == "contentpackage":
            return Package(
                name=root.get("name", "Error"),
                path=Path(package_path),
                local=local_load,
            )

        raise ValueError(f"contentpackage в {path} не найден.")

    @staticmethod
    def _process_xml(file_path):
        AppGlobalsAndConfig.user_config.pop("mod_package_path", None)
        AppGlobalsAndConfig.user_config.pop("mod_package_path_active", None)
        AppGlobalsAndConfig.user_config.pop("mod_package_path_local_active", None)
        AppGlobalsAndConfig.user_config.pop("player_config_path", None)

        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        if content_packages is None:
            return

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            raise ValueError("Не найден тег <regularpackages>")

        for package in regular_packages.findall("package"):
            package_path = package.get("path")
            if package_path:
                path = Path(package_path)
                truncated_path = path.parent

                if str(path).startswith("LocalMods"):
                    PackageLoader._append_config(
                        "mod_package_path_local_active", str(truncated_path)
                    )
                else:
                    PackageLoader._append_config(
                        "mod_package_path_active", str(truncated_path)
                    )

        # Сохраняем player_config_path
        AppGlobalsAndConfig.set_config("player_config_path", file_path)

        AppGlobalsAndConfig.set_config(
            "mod_package_path",
            str(
                Path(
                    *Path(
                        AppGlobalsAndConfig.user_config["mod_package_path_active"][0]
                    ).parts[:-2]
                )
            ),
        )
