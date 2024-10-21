import atexit
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from Code.app_vars import AppGlobalsAndConfig

from .package import Package


class PackageLoader:
    _active_packages: List[Package] = []

    @staticmethod
    def init():
        atexit.register(PackageLoader.save_on_exit)

    @staticmethod
    def load(file_path: str) -> None:
        PackageLoader._active_packages.clear()
        PackageLoader._process_xml(Path(file_path))

    @staticmethod
    def save_on_exit() -> None:
        path = AppGlobalsAndConfig.get_config("barotrauma_dir_path")
        if path:
            PackageLoader.save(path + "/config_player.xml")

    @staticmethod
    def save(file_path: str) -> None:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content_packages = root.find("contentpackages")
        regular_packages = content_packages.find("regularpackages")  # type: ignore

        if regular_packages is not None:
            for child in list(regular_packages):
                regular_packages.remove(child)
        else:
            regular_packages = ET.SubElement(content_packages, "regularpackages")  # type: ignore

        filtered_packages = [
            pkg for pkg in PackageLoader._active_packages if pkg.order is not None
        ]
        for package in sorted(filtered_packages, key=lambda p: p.order):  # type: ignore
            regular_packages.append(ET.Comment(package.name))
            package_element = ET.SubElement(regular_packages, "package")
            package_element.set("path", str(package.path) + "\\filelist.xml")

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ", level=0)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _parse_package(package_path: Path, local_load: bool, order: int) -> Package:
        filelist_path = package_path / "filelist.xml"
        if not filelist_path.exists():
            raise ValueError(f"File {filelist_path} not found")

        tree = ET.parse(filelist_path)
        root = tree.getroot()

        if root.tag != "contentpackage":
            raise ValueError(f"contentpackage in {filelist_path} not found")

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
            raise ValueError("Not found <regularpackages>")

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
