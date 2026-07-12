"""Provider-agnostic disposable mailbox handle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from inboxkit.errors import InboxNotBoundError


@dataclass
class TempInbox:
    """Mailbox handle returned by ``InboxKit.create()`` / provider mint.

    Includes the generated address **and** whatever credentials / session
    material the provider needs to read the inbox again (token, password,
    cookies, sid, …) plus provider-specific extras in ``meta``.

    Use ``to_dict()`` / ``credentials`` for a full serializable snapshot.
    """

    address: str
    provider: str
    token: str = ""
    # Provider-specific opaque state (password, sid, login/domain, cookie, …)
    meta: dict[str, Any] = field(default_factory=dict)
    # Bound at mint time so list/read work without re-passing the router
    _list: Callable[["TempInbox"], list[dict[str, Any]]] | None = field(
        default=None, repr=False, compare=False
    )
    _read: Callable[["TempInbox", dict[str, Any]], str] | None = field(
        default=None, repr=False, compare=False
    )

    # --- identity ----------------------------------------------------------

    @property
    def email(self) -> str:
        """Generated mailbox address (alias of ``address``)."""
        return self.address

    @property
    def local(self) -> str:
        if "local" in self.meta and self.meta["local"]:
            return str(self.meta["local"])
        if "@" in self.address:
            return self.address.split("@", 1)[0]
        return self.address

    @property
    def domain(self) -> str:
        if "domain" in self.meta and self.meta["domain"]:
            return str(self.meta["domain"])
        if "@" in self.address:
            return self.address.split("@", 1)[1]
        return ""

    @property
    def display_name(self) -> str | None:
        value = self.meta.get("display_name")
        return str(value) if value else None

    @property
    def password(self) -> str | None:
        """Account password when the provider uses one (e.g. mail.tm)."""
        for key in ("password", "pass", "passwd"):
            value = self.meta.get(key)
            if value:
                return str(value)
        return None

    @property
    def view_url(self) -> str | None:
        """Web UI hint when the provider exposes one."""
        for key in ("view_hint", "web_url", "site", "url"):
            value = self.meta.get(key)
            if value:
                return str(value)
        return None

    # --- credentials / full dump -------------------------------------------

    @property
    def credentials(self) -> dict[str, Any]:
        """Auth material needed to re-access this inbox.

        Always includes ``email``, ``provider``, ``token``. Adds password /
        session fields when present in ``meta``.
        """
        creds: dict[str, Any] = {
            "email": self.address,
            "address": self.address,
            "provider": self.provider,
            "token": self.token,
        }
        if self.password:
            creds["password"] = self.password
        # Common session / access keys (only if set)
        for key in (
            "sid_token",
            "oturum",
            "cookie",
            "tarih",
            "visitor_id",
            "account_id",
            "login",
            "mailbox",
            "api_key",
            "backend",
        ):
            value = self.meta.get(key)
            if value not in (None, ""):
                creds[key] = value
        # token often duplicated in meta — keep explicit
        if self.meta.get("token") and "token" not in creds:
            creds["token"] = self.meta["token"]
        return creds

    def to_dict(self) -> dict[str, Any]:
        """Full serializable snapshot: email + credentials + every meta detail."""
        return {
            "email": self.address,
            "address": self.address,
            "provider": self.provider,
            "token": self.token,
            "password": self.password,
            "local": self.local,
            "domain": self.domain,
            "display_name": self.display_name,
            "view_url": self.view_url,
            "credentials": self.credentials,
            "meta": dict(self.meta),
        }

    # --- inbox ops ---------------------------------------------------------

    def list_messages(self) -> list[dict[str, Any]]:
        if not self._list:
            raise InboxNotBoundError(
                f"{self.provider}: list_messages not bound",
                code="list_not_bound",
                details={"provider": self.provider, "address": self.address},
            )
        return self._list(self)

    def read_message(self, msg: dict[str, Any]) -> str:
        if not self._read:
            raise InboxNotBoundError(
                f"{self.provider}: read_message not bound",
                code="read_not_bound",
                details={"provider": self.provider, "address": self.address},
            )
        return self._read(self, msg)
