from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class TempMailLolConfig:
    """tempmail.lol API (https://github.com/tempmail-lol/tempmail-api-javascript).

    Free:
      GET  /generate              create inbox {address, token}
      GET  /auth/{token}          list emails (expires → empty/undefined)
    Plus/Ultra (Authorization / API key):
      create with prefix/domain/community
      setWebhook / removeWebhook (Ultra + custom domains)
    No public per-message delete; inboxes expire by tier TTL.
    """

    BASE = "https://api.tempmail.lol"
    PROVIDER = "tempmail.lol"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempMailLolGenerateService(TempMailLolConfig, IProviderGenerateService):
    @abstractmethod
    def create_inbox(
        self,
        *,
        prefix: str | None = None,
        domain: str | None = None,
        community: bool | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def set_webhook(self, url: str, *, api_key: str) -> Any: ...

    @abstractmethod
    def remove_webhook(self, *, api_key: str) -> Any: ...


class ITempMailLolInboxService(TempMailLolConfig, IProviderInboxService):
    @abstractmethod
    def check_inbox(self, token: str) -> list[dict[str, Any]]: ...


ITempMailLolService = ITempMailLolGenerateService
