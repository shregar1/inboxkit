from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class GuerrillaMailConfig:
    """Guerrilla Mail JSON API (https://www.guerrillamail.com/GuerrillaMailAPI.html).

    Functions via GET/POST https://api.guerrillamail.com/ajax.php?f=...
      get_email_address, set_email_user, check_email, get_email_list,
      fetch_email, del_email, forget_me, extend
    """

    BASE = "https://api.guerrillamail.com/ajax.php"
    PROVIDER = "guerrillamail"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class IGuerrillaMailGenerateService(GuerrillaMailConfig, IProviderGenerateService):
    @abstractmethod
    def get_email_address(self, *, lang: str = "en") -> dict[str, Any]: ...

    @abstractmethod
    def set_email_user(self, sid_token: str, email_user: str, *, lang: str = "en") -> dict[str, Any]: ...

    @abstractmethod
    def forget_me(self, inbox: TempInbox) -> Any: ...

    @abstractmethod
    def extend(self, inbox: TempInbox) -> dict[str, Any]: ...


class IGuerrillaMailInboxService(GuerrillaMailConfig, IProviderInboxService):
    @abstractmethod
    def check_email(self, inbox: TempInbox, *, seq: int = 0) -> dict[str, Any]: ...

    @abstractmethod
    def get_email_list(self, inbox: TempInbox, *, offset: int = 0) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_email(self, inbox: TempInbox, email_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def delete_messages(self, inbox: TempInbox, email_ids: list[str | int]) -> list[Any]: ...


IGuerrillaMailService = IGuerrillaMailGenerateService
