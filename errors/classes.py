"""Concrete inboxkit errors (IError).

Shared, HTTP-ish categories live here. Provider-specific types are under
``inboxkit.errors.provider``.
"""

from __future__ import annotations

from inboxkit.abstractions import IError


class TempMailError(IError):
    """Generic inboxkit failure."""


# --- request / client -------------------------------------------------------


class BadInputError(TempMailError):
    """Invalid arguments or malformed input (≈400)."""


class UnauthorizedError(TempMailError):
    """Missing or invalid credentials / token (≈401)."""


class ForbiddenError(TempMailError):
    """Authenticated but not allowed (≈403)."""


class NotFoundError(TempMailError):
    """Requested resource does not exist (≈404)."""


class ConflictError(TempMailError):
    """State conflict, e.g. address already taken (≈409)."""


class UnprocessableError(TempMailError):
    """Semantically invalid request the API cannot process (≈422)."""


class RateLimitError(TempMailError):
    """Too many requests (≈429)."""


# --- time / availability ----------------------------------------------------


class TimeoutError(TempMailError):
    """Operation exceeded its time budget."""


class UnavailableError(TempMailError):
    """Upstream provider or dependency is unavailable (≈503)."""


class InternalError(TempMailError):
    """Unexpected internal / programming fault."""


# --- domain specializations -------------------------------------------------


class UnknownProviderError(BadInputError):
    """Requested provider name is not registered."""


class AllProvidersFailedError(UnavailableError):
    """Every provider in the fallback chain failed to mint."""


class VerifyTimeoutError(TimeoutError):
    """No verify link appeared in the inbox before timeout."""


class InboxNotBoundError(InternalError):
    """TempInbox is missing list/read binders."""
