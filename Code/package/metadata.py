from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Set

from .identifier import Identifier


@dataclass
class IdentifierConflict(Identifier):
    message: str
    level: Literal["warning", "error"]


@dataclass
class MetaData:
    load_order: Optional[int] = None

    mod_version: str = "0.0.0"
    game_version: str = "0.0.0"

    settings: Dict[str, Any] = field(default_factory=dict)
    has_dll: bool = False
    has_cs: bool = False
    has_lua: bool = False

    meta: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    overrides: Optional[Set[str]] = None

    # dependencies
    patches: List[Identifier] = field(default_factory=list)
    requirements: List[Identifier] = field(default_factory=list)
    optionals_requirements: List[Identifier] = field(default_factory=list)
    optionals_patches: List[Identifier] = field(default_factory=list)
    conflicts: List[IdentifierConflict] = field(default_factory=list)
