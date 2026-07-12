"""Provider error contract."""

from __future__ import annotations

from typing import Any

from inboxkit.errors.classes import TempMailError


class IProviderError(TempMailError):
    """Base for disposable-mail provider failures."""

    provider: str | None = None

    def __init__(
        self,
        message: str = "",
        *,
        provider: str | None = None,
        code: str | None = None,
        details: Any = None,
    ) -> None:
        name = provider if provider is not None else type(self).provider
        super().__init__(
            message,
            code=code or type(self).__name__,
            details=details,
        )
        self.provider = name
