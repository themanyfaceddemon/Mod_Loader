import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Union

from .identifier import Identifier
from .metadata import MetaData

logger = logging.getLogger("PackageParsing")


class Package:
    def __init__(
        self,
        path: Union[str, Path],
    ) -> None:
        self.path: Path = Path(path)

        self.identifier: Identifier = Identifier("initing...", None, None)
        self.metadata: MetaData = MetaData()

        self._init_setup()

    def _init_setup(self) -> None:
        self._parse_filelist()

        self._parse_metadata()

        # check file types
        self.metadata.has_lua = self._check_has_file("lua")
        self.metadata.has_cs = self._check_has_file("cs")
        self.metadata.has_dll = self._check_has_file("dll")

    def _check_has_file(self, file_type: str) -> bool:
        return any(self.path.rglob(f"*.{file_type}"))

    def _parse_filelist(self) -> None:
        filelist_path = self.path / "filelist.xml"
        if not filelist_path.exists():
            raise ValueError(f"filelist.xml don't exist for {self.path}")

        tree = ET.parse(str(filelist_path))
        root = tree.getroot()
        if root.tag != "contentpackage":
            raise ValueError(f"Invalid filelist.xml structure for {self.path}")

        if root.get("corepackage", "false").lower() == "true":
            raise RuntimeError(f"Corepackage {self.path}")

        pack_name = root.get("name", None)
        pack_steam_id = root.get("steamworkshopid", None)
        mod_version = root.get("modversion", "Not set")
        game_version = root.get("gameversion", "Not set")

        if pack_name is None:
            raise ValueError(f"For mod {self.path} name is None")

        if pack_steam_id and pack_steam_id.isdecimal():
            pack_steam_id = int(pack_steam_id)
        else:
            pack_steam_id = None

        self.identifier.name = pack_name
        self.identifier.steam_id = pack_steam_id

        self.metadata.mod_version = mod_version
        self.metadata.game_version = game_version

    def _parse_metadata(self) -> None:
        metadata_path = self.path / "metadata.xml"
        if not metadata_path.exists():
            self._load_default_metadata_settings()
            return

        tree = ET.parse(str(metadata_path))
        root = tree.getroot()
        if root.tag != "metadata":
            raise ValueError(f"Invalid metadata.xml structure for {self.path}")

        settings = root.find("settings")
        if settings is not None:
            for setting in settings.findall("setting"):
                name = setting.attrib.get("name")
                value = setting.attrib.get("value")
                if name and value is not None:
                    self.metadata.settings[name] = value.lower() == "true"

        else:
            self._load_default_metadata_settings()

        meta = root.find("meta")
        if meta is not None:
            author = meta.find("author", None)
            author = (
                author.text.strip()
                if isinstance(author, ET.Element)
                and isinstance(author.text, str)
                and author.text.strip()
                else "Unknown"
            )

            license = meta.find("license", None)
            license = (
                license.text.strip()
                if isinstance(license, ET.Element)
                and isinstance(license.text, str)
                and license.text.strip()
                else "Not specified"
            )

            mod_id = meta.find("id", None)
            mod_id = (
                mod_id.text.strip()
                if isinstance(mod_id, ET.Element)
                and isinstance(mod_id.text, str)
                and mod_id.text.strip()
                else None
            )

            warning = meta.find("warning")
            warning = (
                warning.text.strip()
                if isinstance(warning, ET.Element)
                and isinstance(warning.text, str)
                and warning.text.strip()
                else None
            )

            error = meta.find("error")
            error = (
                error.text.strip()
                if isinstance(error, ET.Element)
                and isinstance(error.text, str)
                and error.text.strip()
                else None
            )

            self.identifier.package_id = mod_id
            self.metadata.meta["author"] = author
            self.metadata.meta["license"] = license

            if warning:
                self.metadata.warnings.append(warning)

            if error:
                self.metadata.errors.append(error)

        dependencies = root.find("dependencies")
        if dependencies is not None:
            self.metadata.patches = self._process_dependencies_element(
                dependencies, "patch"
            )
            self.metadata.requirements = self._process_dependencies_element(
                dependencies, "requirement"
            )
            self.metadata.optionals = self._process_dependencies_element(
                dependencies, "optional"
            )
            self.metadata.conflicts = self._process_dependencies_element(
                dependencies, "conflict"
            )

    def _process_dependencies_element(
        self, root: ET.Element, type: str
    ) -> List[Identifier]:
        exit_list: List[Identifier] = []

        for element in root.findall(type):
            element_name = element.attrib.get("name")
            if element_name is None or not element_name.strip():
                raise ValueError(
                    f"Error while parsing metadata dependencies.{type}: {self.path}"
                )

            element_steam_id = element.attrib.get("steamID", None)
            if element_steam_id and element_steam_id.isdecimal():
                element_steam_id = int(element_steam_id)
            else:
                element_steam_id = None

            exit_list.append(
                Identifier(
                    element_name,
                    element_steam_id,
                    element.attrib.get("ID", None),
                )
            )

        return exit_list

    def _load_default_metadata_settings(self) -> None:
        self.metadata.settings["IgnoreLUACheck"] = False
        self.metadata.settings["IgnoreCSDLLCheck"] = False
        self.metadata.settings["DisableCSDLLCheck"] = False
