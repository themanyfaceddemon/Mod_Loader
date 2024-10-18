from pathlib import Path


class Package:
    def __init__(self, name: str, path: Path, local=False) -> None:
        self.name: str = name
        self.path: Path = path
        self.local: bool = local

    def __str__(self) -> str:
        return f"Package: {self.name} | Local: {self.local} | Path: {self.path}"
