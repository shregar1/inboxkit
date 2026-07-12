"""Public router contract — one class for all provider email ops."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Sequence

from inboxkit.abstractions import IService
from inboxkit.enums import RouterMode
from inboxkit.models import TempInbox


class ITempMailRouter(IService):
    """Provider-agnostic facade: sticky or fallback minting."""

    @property
    @abstractmethod
    def mode(self) -> RouterMode:
        """``sticky`` (pinned provider) or ``fallback`` (ordered tries)."""

    @property
    @abstractmethod
    def order(self) -> list[str]:
        """Provider try-order used in fallback mode."""

    @abstractmethod
    def providers(self) -> list[str]:
        """Canonical provider names available to this router."""

    @abstractmethod
    def set_order(self, order: Sequence[str]) -> ITempMailRouter:
        """Set fallback provider order (aliases resolved to canonical)."""

    @abstractmethod
    def create(
        self,
        provider: str | None = None,
        *,
        order: Sequence[str] | None = None,
    ) -> TempInbox:
        """Mint a disposable inbox per current mode (or one-shot provider)."""

    @abstractmethod
    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        """List messages for ``inbox``."""

    @abstractmethod
    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        """Read one message body as a text/html blob."""

    @abstractmethod
    def wait_for_message(
        self,
        inbox: TempInbox,
        *,
        timeout_secs: float = 120,
        poll_every: float = 5,
    ) -> dict[str, Any]:
        """Poll until at least one message arrives; return the newest."""

    @abstractmethod
    def wait_for_link(
        self,
        inbox: TempInbox,
        *,
        timeout_secs: float = 180,
        poll_every: float = 5,
    ) -> str:
        """Poll until a verify-style link appears in a message body."""

    @abstractmethod
    def delete_message(
        self,
        inbox: TempInbox,
        message_id: str | int,
        **kwargs: Any,
    ) -> Any:
        """Delete one message when the provider supports it."""

    @abstractmethod
    def destroy(self, inbox: TempInbox, **kwargs: Any) -> Any:
        """Destroy / forget the mailbox when the provider supports it."""
