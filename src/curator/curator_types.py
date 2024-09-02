from dataclasses import dataclass
from typing import Any


@dataclass
class CuratorRepo:
    name: str
    about: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CuratorRepo):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)
