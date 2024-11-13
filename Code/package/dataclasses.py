import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from Code.app_vars import AppConfig
from Code.xml_object import XMLObject

from .id_parser import IDParser

logger = logging.getLogger("ModBuild")


@dataclass
class Identifier:
    name: str
    steam_id: Optional[str]

    @property
    def id(self) -> str:
        if self.steam_id:
            return self.steam_id
        return self.name

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Identifier):
            return self.id == value.id

        elif isinstance(value, str):
            return self.id == value

        return False

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Identifier(name={self.name}, steam_id={self.steam_id})"


@dataclass
class Dependencie(Identifier):
    dep_type: Literal[
        "patch",
        "optionalPatch",
        "requirement",
        "optionalRequirement",
        "requiredAnyOrder",
        "conflict",
    ]
    add_attribute: Dict[str, str]

    def __str__(self) -> str:
        additional_attributes = ", ".join(
            f"{k}={v}" for k, v in self.add_attribute.items()
        )
        return f"Dependencie(type={self.dep_type}, id={self.id}, attributes={{{additional_attributes}}})"

    def __repr__(self) -> str:
        return (
            f"Dependencie(name={self.name}, steam_id={self.steam_id}, "
            f"dep_type={self.dep_type}, add_attribute={self.add_attribute})"
        )

    @staticmethod
    def is_valid_type(value: str):
        return value in {
            "patch",
            "optionalPatch",
            "requirement",
            "optionalRequirement",
            "requiredAnyOrder",
            "conflict",
        }


@dataclass
class Metadata:
    mod_version: str
    game_version: str

    author_name: str
    license: str

    warnings: List[str]
    errors: List[str]

    dependencies: List[Dependencie]

    @staticmethod
    def create_empty() -> "Metadata":
        return Metadata(
            "base-not-set",
            "base-not-set",
            "base-unknown",
            "base-not-specified",
            [],
            [],
            [],
        )

    def __str__(self) -> str:
        dependencies_str = ", ".join(str(dep) for dep in self.dependencies)
        warnings_str = "; ".join(self.warnings)
        errors_str = "; ".join(self.errors)
        return (
            f"Metadata(mod_version={self.mod_version}, game_version={self.game_version}, "
            f"author={self.author_name}, license={self.license}, warnings=[{warnings_str}], "
            f"errors=[{errors_str}], "
            f"dependencies=[{dependencies_str}])"
        )

    def __repr__(self) -> str:
        return (
            f"Metadata(mod_version={self.mod_version}, "
            f"game_version={self.game_version}, author_name={self.author_name}, license={self.license}, "
            f"warnings={self.warnings}, errors={self.errors}, "
            f"dependencies={self.dependencies})"
        )


@dataclass
class ModUnit(Identifier):
    local: bool
    load_order: Optional[int]

    metadata: Metadata

    use_lua: bool
    use_cs: bool

    settings: Dict[str, Any]

    add_id: set[str]
    override_id: set[str]

    @staticmethod
    def create_empty() -> "ModUnit":
        return ModUnit(
            "base-not-set",
            None,
            False,
            None,
            Metadata.create_empty(),
            False,
            False,
            {},
            set(),
            set(),
        )

    @staticmethod
    def build_by_path(path: (Path | str)) -> Optional["ModUnit"]:
        path = Path(path)

        obj = ModUnit.create_empty()

        if path.parts[0] == "LocalMods":
            obj.local = True
            new_path = AppConfig.get("barotrauma_dir", None)
            if new_path is None:
                raise ValueError("Game dir not set!")

            path = Path(new_path / path)

        ModUnit.parse_filelist(obj, path)

        obj.use_lua = ModUnit.has_file(path, ".[Ll][Uu][Aa]")
        obj.use_cs = any(
            [
                ModUnit.has_file(path, ".[Cc][Ss]"),
                ModUnit.has_file(path, ".[Dd][Ll][Ll]"),
            ]
        )

        ModUnit.parse_files(obj, path)
        ModUnit.parse_metadata(obj, path)

        return obj

    @staticmethod
    def has_file(path: Path, extension: str) -> bool:
        for file in path.rglob(f"*{extension}"):
            return True

        return False

    @staticmethod
    def parse_filelist(obj: "ModUnit", path: Path) -> None:
        file_list_path = path / "filelist.xml"
        if not file_list_path.exists():
            raise ValueError(f"{file_list_path} don't exsist")

        xml_obj = XMLObject.load_file(file_list_path)
        if not xml_obj.root:
            raise ValueError(f"{file_list_path} invalid xml struct")

        xml_obj = xml_obj.root
        obj.name = xml_obj.attributes.get("name", "Something went rong")
        obj.steam_id = xml_obj.attributes.get("steamworkshopid")
        obj.metadata.game_version = xml_obj.attributes.get(
            "gameversion", "base-not-specified"
        )
        obj.metadata.mod_version = xml_obj.attributes.get(
            "modversion", "base-not-specified"
        )

    @staticmethod
    def parse_files(obj: "ModUnit", path: Path) -> None:
        xml_files_paths = path.rglob("*.[Xx][Mm][Ll]")

        for xml_file_path in xml_files_paths:
            if xml_file_path.name.lower() in [
                "filelist.xml",
                "metadata.xml",
                "file_list.xml",
                "files_list.xml",
            ]:
                continue

            try:
                xml_obj = XMLObject.load_file(xml_file_path)
                if not xml_obj.root:
                    logger.warning(f"File {xml_file_path} is empty")
                    continue

                xml_obj = xml_obj.root

                id_parser_unit = IDParser.get_ids(xml_obj)
                obj.add_id.update(id_parser_unit.add_id)
                obj.override_id.update(id_parser_unit.override_id)

            except Exception as err:
                logger.error(str(err) + f"\n|Mod: {obj!r}")

    @staticmethod
    def parse_metadata(obj: "ModUnit", path: Path) -> None:
        metadata_path = path / "metadata.xml"

        if not metadata_path.exists():
            search_pattern = f"{obj.id}.xml"
            found_files = list(
                (AppConfig.get_data_root() / "InternalLibrary").rglob(search_pattern)
            )

            if found_files:
                metadata_path = found_files[0]
            else:
                return

        xml_obj = XMLObject.load_file(metadata_path)
        if not xml_obj.root:
            raise ValueError(f"Empty metadata.xml for {obj.id}!")
        xml_obj = xml_obj.root

        for element in xml_obj.iter_non_comment_childrens():
            element_name_lower = element.name.lower()

            if element_name_lower == "settings":
                for ch in element.iter_non_comment_childrens():
                    setting_name = ch.attributes.get("name")
                    if setting_name:
                        obj.settings[setting_name] = ch.attributes.get("value")

            if element_name_lower == "meta":
                for ch in element.iter_non_comment_childrens():
                    ch_name_lower = ch.name.lower()
                    if ch_name_lower == "author":
                        obj.metadata.author_name = ch.content
                    elif ch_name_lower == "license":
                        obj.metadata.license = ch.content
                    elif ch_name_lower == "warning":
                        obj.metadata.warnings.extend(ch.content.strip().splitlines())
                    elif ch_name_lower == "error":
                        obj.metadata.errors.extend(ch.content.strip().splitlines())

            if element_name_lower == "dependencies":
                dependencies = []
                for ch in element.iter_non_comment_childrens():
                    dep_type = ch.name

                    if not Dependencie.is_valid_type(dep_type):
                        raise ValueError(
                            f"Invalid dependency type: '{dep_type}' in element {ch}"
                        )

                    name = ch.attributes.get("name")
                    steam_id = ch.attributes.get("steamID")

                    if not name:
                        raise ValueError(
                            f"Dependency element missing 'name' attribute in element {ch}"
                        )

                    if not steam_id:
                        raise ValueError(
                            f"Dependency element missing 'steamID' attribute in element {ch}"
                        )

                    add_attributes = ch.attributes.copy()
                    add_attributes.pop("steamID", None)

                    dependency = Dependencie(
                        name=name,
                        steam_id=steam_id,
                        dep_type=dep_type,  # type: ignore
                        add_attribute=add_attributes,
                    )
                    dependencies.append(dependency)

                obj.metadata.dependencies = dependencies
