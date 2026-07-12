from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class SecMailConfig:
    """1secmail public API (https://www.1secmail.com/api/v1/).

    Actions:
      genRandomMailbox&count=N
      getDomainList
      getMessages&login=&domain=
      readMessage&login=&domain=&id=
      download&login=&domain=&id=&file=
    No public delete/update endpoints (messages expire server-side).
    """

    BASE = "https://www.1secmail.com/api/v1/"
    PROVIDER = "1secmail"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ISecMailGenerateService(SecMailConfig, IProviderGenerateService):
    @abstractmethod
    def list_domains(self) -> list[str]: ...

    @abstractmethod
    def gen_random_mailbox(self, count: int = 1) -> list[str]: ...


class ISecMailInboxService(SecMailConfig, IProviderInboxService):
    @abstractmethod
    def get_message(self, inbox: TempInbox, message_id: str | int) -> dict[str, Any]: ...

    @abstractmethod
    def download_attachment(
        self, inbox: TempInbox, message_id: str | int, filename: str
    ) -> bytes: ...


ISecMailService = ISecMailGenerateService
