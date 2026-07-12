from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.secmail import SecMailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.secmail.abstraction import ISecMailInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility
from inboxkit.utilities import HttpUtility, VerifyUtility


class SecMailInboxService(ISecMailInboxService):
    def _parts(self, inbox: TempInbox) -> tuple[str, str]:
        login = str(inbox.meta.get("login") or "")
        domain = str(inbox.meta.get("domain") or "")
        if not login or not domain:
            login, domain = inbox.address.split("@", 1)
        return login, domain

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        login, domain = self._parts(inbox)
        data = HttpUtility.json(
            "GET",
            f"{self.BASE}?action=getMessages&login={login}&domain={domain}",
        )
        if not isinstance(data, list):
            return []
        return [x for x in data if isinstance(x, dict)]

    def get_message(self, inbox: TempInbox, message_id: str | int) -> dict[str, Any]:
        login, domain = self._parts(inbox)
        data = HttpUtility.json(
            "GET",
            f"{self.BASE}?action=readMessage&login={login}&domain={domain}&id={message_id}",
        )
        if not isinstance(data, dict):
            raise SecMailError(f"1secmail: bad message: {data}")
        return data

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = msg.get("id")
        if mid is None:
            return VerifyUtility.blob_from_parts(msg.get("subject"), msg.get("from"))
        try:
            full = self.get_message(inbox, mid)
        except Exception:
            return VerifyUtility.blob_from_parts(msg.get("subject"), msg.get("from"))
        return VerifyUtility.blob_from_parts(
            full.get("subject"),
            full.get("from"),
            full.get("textBody"),
            full.get("htmlBody"),
            full.get("body"),
        )

    def download_attachment(
        self, inbox: TempInbox, message_id: str | int, filename: str
    ) -> bytes:
        login, domain = self._parts(inbox)
        url = (
            f"{self.BASE}?action=download&login={login}&domain={domain}"
            f"&id={message_id}&file={filename}"
        )
        return HttpUtility.bytes("GET", url)
