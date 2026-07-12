"""Typed error hierarchy."""

from __future__ import annotations

from inboxkit.abstractions import IError
from inboxkit.errors.classes import (
    AllProvidersFailedError,
    BadInputError,
    ConflictError,
    ForbiddenError,
    InboxNotBoundError,
    InternalError,
    NotFoundError,
    RateLimitError,
    TempMailError,
    TimeoutError,
    UnauthorizedError,
    UnavailableError,
    UnknownProviderError,
    UnprocessableError,
    VerifyTimeoutError,
)
from inboxkit.errors.provider import (
    GuerrillaMailError,
    IProviderError,
    MailDropError,
    MailTmError,
    SecMailError,
    SmailProError,
    TempMailAppError,
    TempMailLolError,
    TempMailOrgError,
    TempailError,
    TempmailNetError,
    TempyError,
)

# Back-compat alias
ProviderError = IProviderError

__all__ = [
    "AllProvidersFailedError",
    "BadInputError",
    "ConflictError",
    "ForbiddenError",
    "GuerrillaMailError",
    "IError",
    "IProviderError",
    "InboxNotBoundError",
    "InternalError",
    "MailDropError",
    "MailTmError",
    "NotFoundError",
    "ProviderError",
    "RateLimitError",
    "SecMailError",
    "SmailProError",
    "TempMailAppError",
    "TempMailError",
    "TempMailLolError",
    "TempMailOrgError",
    "TempailError",
    "TempmailNetError",
    "TempyError",
    "TimeoutError",
    "UnauthorizedError",
    "UnavailableError",
    "UnknownProviderError",
    "UnprocessableError",
    "VerifyTimeoutError",
]
