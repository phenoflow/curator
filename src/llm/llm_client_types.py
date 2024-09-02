from enum import Enum


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
