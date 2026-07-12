"""Package interface contracts (I* markers / bases).

Error contracts live in ``inboxkit.errors``.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Any


class IAbstraction(ABC):
    """Base for domain model abstractions."""


class IUtility(ABC):
    """Base for stateless utility helpers (prefer @staticmethod / classmethods)."""


class IService(ABC):
    """Base for orchestration / application services."""


class IFactory(ABC):
    """Base for object factories."""


class IConstant(ABC):
    """Base for constant namespaces (class attributes only)."""

    def __init__(self) -> None:
        raise TypeError(f"{type(self).__name__} is a constant namespace; do not instantiate")


class IError(Exception, ABC):
    """Base for all tempmail package errors."""

    def __init__(self, message: str = "", *, code: str | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or type(self).__name__
        self.details = details

    def __str__(self) -> str:
        if self.message:
            return self.message
        return self.code


class IEnum(Enum):
    """Base enum for the tempmail package."""

    @classmethod
    def values(cls) -> list[Any]:
        return [m.value for m in cls]

    @classmethod
    def names(cls) -> list[str]:
        return [m.name for m in cls]
