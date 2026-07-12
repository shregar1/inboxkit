from __future__ import annotations

from abc import abstractmethod
from typing import Any, Literal

from inboxkit.models import TempInbox
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)

MailKind = Literal["email", "gmail", "outlook"]


class SmailProConfig:
    """SmailPro / Sonjj temporary email API.

    Docs:
      https://smailpro.com/temporary-email
      https://smailpro.com/api
      https://sonjj.com/docs/
      https://smailpro.com/features

    Base: https://app.sonjj.com
    Auth: X-Api-Key (from https://my.sonjj.com) — env ``SMAILPRO_API_KEY``

    Temp email (custom domains):
      GET /v1/temp_email/domains
      GET /v1/temp_email/create?email=&expiry_minutes=
      GET /v1/temp_email/inbox?email=
      GET /v1/temp_email/message?email=&mid=
      GET /v1/temp_email/attachments?email=&mid=

    Temp Gmail:
      GET /v1/temp_gmail/list|random|inbox|message|remove_message

    Temp Outlook:
      GET /v1/temp_outlook/list|random|inbox|message
    """

    BASE = "https://app.sonjj.com"
    PROVIDER = "smailpro"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER


class ISmailProGenerateService(SmailProConfig, IProviderGenerateService):
    @abstractmethod
    def list_domains(self) -> list[str]: ...

    @abstractmethod
    def create_email(self, email: str, *, expiry_minutes: int = 0) -> dict[str, Any]: ...

    @abstractmethod
    def random_gmail(
        self, *, type: Literal["real", "alias"] = "alias", password: str | None = None
    ) -> dict[str, Any]: ...

    @abstractmethod
    def list_gmail(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        type: Literal["real", "alias"] = "alias",
        password: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def random_outlook(
        self, *, type: Literal["real", "alias"] = "alias", password: str | None = None
    ) -> dict[str, Any]: ...

    @abstractmethod
    def list_outlook(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        type: Literal["real", "alias"] = "alias",
        password: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def mint(
        self,
        *,
        kind: MailKind = "email",
        domain: str | None = None,
        email: str | None = None,
        expiry_minutes: int = 0,
        gmail_type: Literal["real", "alias"] = "alias",
    ) -> TempInbox: ...


class ISmailProInboxService(SmailProConfig, IProviderInboxService):
    @abstractmethod
    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def remove_gmail_message(self, inbox: TempInbox, message_id: str) -> Any: ...

    @abstractmethod
    def list_attachments(self, inbox: TempInbox, message_id: str) -> Any: ...


ISmailProService = ISmailProGenerateService
