import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Union

from Code.app_vars import AppGlobalsAndConfig
from Code.loc import Localization as loc

from .identifier import Identifier
from .metadata import IdentifierConflict, MetaData
from .override_processor import OverrideProcessor

logger = logging.getLogger("PackageParsing")


class Package:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path: Path = Path(path)
        self.identifier: Identifier = Identifier("initing...", None, None)
        self.metadata: MetaData = MetaData()
        self._init_setup()

    def _init_setup(self) -> None:
        self._parse_filelist()
        self.parse_metadata()

        self.metadata.has_lua = self._check_has_file("lua")
        self.metadata.has_cs = self._check_has_file("cs")
        self.metadata.has_dll = self._check_has_file("dll")

        OverrideProcessor.process(self.metadata, self.path)

    def _check_has_file(self, file_type: str) -> bool:
        return any(self.path.rglob(f"*.{file_type}"))

    def _parse_filelist(self) -> None:
        filelist_path = self.path / "filelist.xml"
        if not filelist_path.exists():
            raise ValueError(f"filelist.xml does not exist at path {self.path}")

        tree = ET.parse(str(filelist_path))
        root = tree.getroot()
        if root.tag != "contentpackage":
            raise ValueError(f"Invalid filelist.xml structure for {self.path}")

        if root.get("corepackage", "false").lower() == "true":
            raise RuntimeError(f"The {self.path} mod is Corepackage")

        pack_name = root.get("name")
        pack_steam_id = root.get("steamworkshopid")
        mod_version = root.get("modversion", "Not set")
        game_version = root.get("gameversion", "Not set")

        if pack_name is None:
            raise ValueError(f"The mod name is missing for {self.path}")

        self.identifier.name = pack_name
        self.identifier.steam_id = (
            int(pack_steam_id) if pack_steam_id and pack_steam_id.isdecimal() else None
        )
        self.metadata.mod_version = mod_version
        self.metadata.game_version = game_version

    def parse_metadata(self) -> None:
        metadata_path = self.path / "metadata.xml"
        if not metadata_path.exists():
            self._load_default_metadata_from_internal_library()
            return

        tree = ET.parse(str(metadata_path))
        root = tree.getroot()
        if root.tag != "metadata":
            raise ValueError(f"Invalid metadata.xml structure for {self.path}")

        self._parse_settings(root.find("settings"))
        self._parse_meta(root.find("meta"))
        self._parse_dependencies(root.find("dependencies"))

    def _parse_settings(self, settings: Optional[ET.Element]) -> None:
        if settings is None:
            self._load_default_metadata_settings()
            return

        for setting in settings.findall("setting"):
            name = setting.attrib.get("name")
            value = setting.attrib.get("value")
            if name and value is not None:
                self.metadata.settings[name] = value.lower() == "true"

    def _parse_meta(self, meta: Optional[ET.Element]) -> None:
        if meta is None:
            return

        self.metadata.meta["author"] = self._get_text_or_default(  # type: ignore
            meta, "author", loc.get_string("base-unknown")
        )
        self.metadata.meta["license"] = self._get_text_or_default(  # type: ignore
            meta, "license", loc.get_string("not-specified")
        )
        self.identifier.package_id = self._get_text_or_default(meta, "id", None)

        warning = self._get_text_or_default(meta, "warning")
        if warning:
            self.metadata.warnings.append(warning)

        error = self._get_text_or_default(meta, "error")
        if error:
            self.metadata.errors.append(error)

    def _parse_dependencies(self, dependencies: Optional[ET.Element]) -> None:
        if dependencies is None:
            return

        self.metadata.patches = self._process_dependencies_element(
            dependencies, "patch"
        )

        self.metadata.requirements = self._process_dependencies_element(
            dependencies, "requirement"
        )

        self.metadata.optionals_requirements = self._process_dependencies_element(
            dependencies, "optionalRequirement"
        )

        self.metadata.optionals_patches = self._process_dependencies_element(
            dependencies, "optionalPatch"
        )

        self.metadata.conflicts = self._process_dependencies_conflict(
            dependencies, "conflict"
        )

    def _process_dependencies_element(
        self, root: ET.Element, type: str
    ) -> List[Identifier]:
        result: List[Identifier] = []

        for element in root.findall(type):
            element_name = element.attrib.get("name")
            if not element_name or not element_name.strip():
                raise ValueError(
                    f"Error while parsing dependencies.{type}"
                    f"Path: {self.path}"
                    f"Missing or empty name in element: {ET.tostring(element, encoding='utf-8')}"
                )

            element_steam_id = element.attrib.get("steamID")
            steam_id = (
                int(element_steam_id)
                if element_steam_id and element_steam_id.isdecimal()
                else None
            )

            result.append(
                Identifier(element_name.strip(), steam_id, element.attrib.get("ID"))
            )

        return result

    def _process_dependencies_conflict(
        self, root: ET.Element, type: str
    ) -> List[IdentifierConflict]:
        result: List[IdentifierConflict] = []

        for element in root.findall(type):
            element_name = element.attrib.get("name")
            if not element_name or not element_name.strip():
                raise ValueError(
                    f"Error while parsing dependencies.{type}"
                    f"Path: {self.path}"
                    f"Missing or empty name in element: {ET.tostring(element, encoding='utf-8')}"
                )

            element_steam_id = element.attrib.get("steamID")
            steam_id = (
                int(element_steam_id)
                if element_steam_id and element_steam_id.isdecimal()
                else None
            )
            level = element.attrib.get("level", "error")
            if level not in {"warning", "error"}:
                logger.error(("Error in conflict element\n" f"|Path: {self.path}"))
                level = "error"

            result.append(
                IdentifierConflict(
                    element_name.strip(),
                    steam_id,
                    element.attrib.get("ID"),
                    element.attrib.get("message", "Incompatible modifications"),
                    level,  # type: ignore
                )
            )

        return result

    def _get_text_or_default(
        self, parent: ET.Element, tag: str, default: Optional[str] = None
    ) -> Optional[str]:
        element = parent.find(tag)
        if (
            isinstance(element, ET.Element)
            and isinstance(element.text, str)
            and element.text.strip()
        ):
            return element.text.strip()
        return default

    def _load_default_metadata_settings(self) -> None:
        self.metadata.settings["IgnoreLUACheck"] = False
        self.metadata.settings["DisableCSDLLCheck"] = False

    def _load_default_metadata_from_internal_library(self) -> None:
        if self.identifier.steam_id is None:
            self._load_default_metadata_settings()
            return

        internal_library_meta_path = (
            AppGlobalsAndConfig.get_data_root()
            / f"InternalLibrary/{self.identifier.steam_id}.xml"
        )
        if not internal_library_meta_path.exists():
            self._load_default_metadata_settings()
            return

        tree = ET.parse(str(internal_library_meta_path))
        root = tree.getroot()
        self._parse_settings(root.find("settings"))
        self._parse_meta(root.find("meta"))
        self._parse_dependencies(root.find("dependencies"))

    def __str__(self) -> str:
        return (
            f"Path: {self.path}\n"
            f"Identifier: {self.identifier}\n"
            f"Metadata:\n"
            f"  Load Order: {self.metadata.load_order}\n"
            f"  Local: {self.metadata.local}\n"
            f"  Mod Version: {self.metadata.mod_version}\n"
            f"  Game Version: {self.metadata.game_version}\n"
            f"  Settings: {self.metadata.settings}\n"
            f"  Has DLL: {self.metadata.has_dll}\n"
            f"  Has CS: {self.metadata.has_cs}\n"
            f"  Has Lua: {self.metadata.has_lua}\n"
            f"  Meta: {self.metadata.meta}\n"
            f"  Warnings: {self.metadata.warnings}\n"
            f"  Errors: {self.metadata.errors}\n"
            f"  Overrides: {self.metadata.overrides}\n"
            f"  Patches: {[str(patch) for patch in self.metadata.patches]}\n"
            f"  Requirements: {[str(req) for req in self.metadata.requirements]}\n"
            f"  Optional Requirements: {[str(opt_req) for opt_req in self.metadata.optionals_requirements]}\n"
            f"  Optional Patches: {[str(opt_patch) for opt_patch in self.metadata.optionals_patches]}\n"
            f"  Conflicts: {[str(conflict) for conflict in self.metadata.conflicts]}"
        )
