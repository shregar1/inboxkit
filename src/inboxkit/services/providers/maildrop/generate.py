from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.maildrop import MailDropError
from inboxkit.models import TempInbox
from inboxkit.services.providers.maildrop.abstraction import IMailDropGenerateService
from inboxkit.services.providers.maildrop.inbox import MailDropInboxService
from inboxkit.utilities import HttpUtility, NameUtility


class MailDropGenerateService(IMailDropGenerateService):
    def _graphql(self, query: str) -> dict[str, Any]:
        data = HttpUtility.json("POST", self.GRAPHQL, body={"query": query})
        if isinstance(data, dict) and data.get("errors"):
            err = data["errors"][0]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise MailDropError(f"maildrop graphql: {msg}")
        return data if isinstance(data, dict) else {}

    def ping(self, message: str = "hello") -> str:
        data = self._graphql(f'{{ ping(message: "{message}") }}')
        return str((data.get("data") or {}).get("ping") or "")

    def statistics(self) -> dict[str, Any]:
        data = self._graphql("{ statistics { blocked saved } }")
        stats = (data.get("data") or {}).get("statistics") or {}
        return stats if isinstance(stats, dict) else {}

    def status(self) -> str:
        data = self._graphql("{ status }")
        return str((data.get("data") or {}).get("status") or "")

    def altinbox(self, mailbox: str) -> str:
        data = self._graphql(f'{{ altinbox(mailbox: "{mailbox}") }}')
        return str((data.get("data") or {}).get("altinbox") or "")

    def mint(self) -> TempInbox:
        mailbox = NameUtility.realistic_local().replace(".", "")
        address = f"{mailbox}@{self.DOMAIN}"
        inbox_svc = MailDropInboxService()
        return TempInbox(
            address=address,
            provider=self.PROVIDER,
            token=mailbox,
            meta={"mailbox": mailbox},
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
