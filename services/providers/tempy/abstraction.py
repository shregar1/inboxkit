from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class TempyConfig:
    """tempy.email Developer API (https://tempy.email/developers).

    Base: https://tempy.email/api/v1
      POST   /mailbox                 create (optional domain/webhook; X-Api-Key optional)
      GET    /mailbox/{address}       status / TTL
      GET    /mailbox/{address}/messages
      DELETE /mailbox/{address}       deactivate
    """

    BASE = "https://tempy.email"
    API = "https://tempy.email/api/v1"
    PROVIDER = "tempy.email"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempyGenerateService(TempyConfig, IProviderGenerateService):
    @abstractmethod
    def create_mailbox(
        self,
        *,
        domain: str | None = None,
        webhook_url: str | None = None,
        webhook_format: str = "json",
        api_key: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def get_mailbox(self, address: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_mailbox(self, address: str) -> None: ...


class ITempyInboxService(TempyConfig, IProviderInboxService):
    pass


ITempyService = ITempyGenerateService
