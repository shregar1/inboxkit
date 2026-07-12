from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class TempMailAppConfig:
    """temp-mail.app — no published OpenAPI; reverse-engineered site routes.

    Observed same-origin endpoints (may change without notice):
      GET /api/mail/address?refresh=&expire=&part=
      GET /api/mail/list?part=
    Identity via visitor-id request header (session cookie substitute).
    No documented public delete/update/message-id APIs.
    """

    BASE = "https://temp-mail.app"
    PROVIDER = "temp-mail.app"
    UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    )

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ITempMailAppGenerateService(TempMailAppConfig, IProviderGenerateService):
    @abstractmethod
    def create_address(
        self, *, expire_minutes: int = 1440, refresh: bool = True
    ) -> dict[str, Any]: ...


class ITempMailAppInboxService(TempMailAppConfig, IProviderInboxService):
    pass


ITempMailAppService = ITempMailAppGenerateService
