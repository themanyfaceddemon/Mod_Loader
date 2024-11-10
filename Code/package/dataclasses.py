from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional

from Code.app_vars import AppConfig
from Code.xml_object import XMLComment, XMLElement, XMLObject
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
            try:
                xml_obj = XMLObject.load_file(xml_file_path)
                if not xml_obj.root:
                    logger.warning(f"File {xml_file_path} is empty")
                    continue

                xml_obj = xml_obj.root

                # TODO
            except Exception as err:
                logger.error(err)
