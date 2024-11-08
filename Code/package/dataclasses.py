from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional
from Code.app_vars import AppConfig


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

            path = Path(new_path)

        # TODO: get name, steamID viva filelist.xml

        # TODO: Build metadata

        # TODO: Get add_id and override_id
