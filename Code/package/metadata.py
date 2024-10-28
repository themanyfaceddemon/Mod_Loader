from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from .identifier import Identifier


@dataclass
class MetaData:
    load_order: Optional[int] = None

    mod_version: str = "0.0.0"
    game_version: str = "0.0.0"

    settings: Dict[str, Any] = {}
    has_dll: bool = False
    has_cs: bool = False
    has_lua: bool = False

    meta: Dict[str, str] = {}
    warnings: List[str] = []
    errors: List[str] = []

    overrides: Optional[Set[str]] = None

    # dependencies
    patches: List[Identifier] = []
    requirements: List[Identifier] = []
    optionals: List[Identifier] = []
    conflicts: List[Identifier] = []
