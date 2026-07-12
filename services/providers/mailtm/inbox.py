from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.mailtm import MailTmError
from inboxkit.models import TempInbox
from inboxkit.services.providers.mailtm.abstraction import IMailTmInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class MailTmInboxService(IMailTmInboxService):
    """mail.tm messages / sources (public API)."""

    @staticmethod
    def _as_list(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            items = data.get("hydra:member") or data.get("member") or []
            return [x for x in items if isinstance(x, dict)]
        return []

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        return self._as_list(HttpUtility.json("GET", f"{self.BASE}/messages", token=inbox.token))

    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        data = HttpUtility.json("GET", f"{self.BASE}/messages/{message_id}", token=inbox.token)
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad message: {data}")
        return data

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("id") or "")
        if not mid:
            return VerifyUtility.blob_from_parts(msg.get("subject"), msg.get("intro"))
        full = self.get_message(inbox, mid)
        return VerifyUtility.blob_from_parts(
            full.get("subject"),
            full.get("intro"),
            full.get("text"),
            full.get("html"),
            msg.get("subject"),
            msg.get("intro"),
        )

    def delete_message(self, inbox: TempInbox, message_id: str) -> None:
        HttpUtility.json("DELETE", f"{self.BASE}/messages/{message_id}", token=inbox.token)

    def mark_seen(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        data = HttpUtility.json(
            "PATCH",
            f"{self.BASE}/messages/{message_id}",
            body={"seen": True},
            token=inbox.token,
            content_type="application/merge-patch+json",
        )
        return data if isinstance(data, dict) else {"seen": True}

    def get_source(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        data = HttpUtility.json("GET", f"{self.BASE}/sources/{message_id}", token=inbox.token)
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad source: {data}")
        return data
