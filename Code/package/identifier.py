from dataclasses import dataclass
from typing import Optional


@dataclass
class Identifier:
    name: str
    steam_id: Optional[int]
    package_id: Optional[str]

    @property
    def id(self) -> str:
        return str(self.steam_id) or self.package_id or self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Identifier):
            return (
                (self.steam_id == other.steam_id)
                or (self.package_id == other.package_id)
                or (self.name == other.name)
            )

        elif isinstance(other, int):
            return self.steam_id == other

        elif isinstance(other, str):
            return self.package_id == other or self.name == other

        return False

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return f"Identifier(name={self.name}, steam_id={self.steam_id}, package_id={self.package_id})"
