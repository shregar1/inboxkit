from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.maildrop import MailDropError
from inboxkit.models import TempInbox
from inboxkit.services.providers.maildrop.abstraction import IMailDropInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class MailDropInboxService(IMailDropInboxService):
    def _graphql(self, query: str) -> dict[str, Any]:
        data = HttpUtility.json("POST", self.GRAPHQL, body={"query": query})
        if isinstance(data, dict) and data.get("errors"):
            err = data["errors"][0]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise MailDropError(f"maildrop graphql: {msg}")
        return data if isinstance(data, dict) else {}

    def _mailbox(self, inbox: TempInbox) -> str:
        return str(inbox.meta.get("mailbox") or inbox.token)

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        mailbox = self._mailbox(inbox)
        data = self._graphql(
            f'{{ inbox(mailbox:"{mailbox}") {{ id mailfrom subject date }} }}'
        )
        inbox_data = (data.get("data") or {}).get("inbox") or []
        if not isinstance(inbox_data, list):
            return []
        return [x for x in inbox_data if isinstance(x, dict)]

    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        mailbox = self._mailbox(inbox)
        data = self._graphql(
            f'{{ message(mailbox:"{mailbox}", id:"{message_id}") '
            f"{{ id subject mailfrom html data date }} }}"
        )
        message = (data.get("data") or {}).get("message") or {}
        if not isinstance(message, dict):
            raise MailDropError(f"maildrop: message not found: {message_id}")
        return message

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("id") or "")
        base = VerifyUtility.blob_from_parts(msg.get("subject"), msg.get("mailfrom"))
        if not mid:
            return base
        message = self.get_message(inbox, mid)
        return VerifyUtility.blob_from_parts(base, message.get("subject"), message.get("html"), message.get("data"))

    def delete_message(self, inbox: TempInbox, message_id: str) -> bool:
        mailbox = self._mailbox(inbox)
        data = self._graphql(
            f'mutation {{ delete(mailbox:"{mailbox}", id:"{message_id}") }}'
        )
        return bool((data.get("data") or {}).get("delete"))
