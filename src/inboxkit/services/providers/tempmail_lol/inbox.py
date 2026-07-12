from __future__ import annotations

from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.tempmail_lol.abstraction import ITempMailLolInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class TempMailLolInboxService(ITempMailLolInboxService):
    def check_inbox(self, token: str) -> list[dict[str, Any]]:
        data = HttpUtility.json("GET", f"{self.BASE}/auth/{token}")
        if data is None:
            return []
        items = data.get("email") or data.get("messages") or data.get("data") or []
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        for i, x in enumerate(items):
            if isinstance(x, dict):
                msg = dict(x)
                msg.setdefault("id", str(x.get("id") or x.get("_id") or i))
                out.append(msg)
        return out

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        return self.check_inbox(inbox.token)

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        return VerifyUtility.blob_from_parts(
            msg.get("subject"), msg.get("body"), msg.get("html"), msg.get("text"), msg.get("from")
        )
