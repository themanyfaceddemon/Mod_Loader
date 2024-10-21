import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from .package import Package


class PackageLoader:
    _active_packages: List[Package] = []

    @staticmethod
    def load(file_path: str) -> None:
        PackageLoader._active_packages.clear()
        PackageLoader._process_xml(Path(file_path))

    @staticmethod
    def _parse_package(package_path: Path, local_load: bool, order: int) -> Package:
        filelist_path = package_path / "filelist.xml"
        if not filelist_path.exists():
            raise ValueError(f"Файл {filelist_path} не найден.")

        tree = ET.parse(filelist_path)
        root = tree.getroot()

        if root.tag != "contentpackage":
            raise ValueError(f"contentpackage в {filelist_path} не найден.")

        return Package(
            name=root.get("name", "Error"),
            path=package_path,
            local=local_load,
            order=order,
        )

    @staticmethod
    def _process_xml(file_path: Path) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        if content_packages is None:
            return

        regular_packages = content_packages.find("regularpackages")
        if regular_packages is None:
            raise ValueError("Не найден тег <regularpackages>")

        PackageLoader._load_packages(regular_packages)

    @staticmethod
    def _load_packages(regular_packages: ET.Element) -> None:
        order = 0
        for package in regular_packages.findall("package"):
            order += 1
            package_path = package.get("path")
            if package_path:
                path = Path(package_path)

                local_load = str(path).startswith("LocalMods")
                PackageLoader._active_packages.append(
                    PackageLoader._parse_package(path.parent, local_load, order)
                )
