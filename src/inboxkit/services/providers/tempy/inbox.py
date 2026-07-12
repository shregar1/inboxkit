from __future__ import annotations

import urllib.parse
from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.tempy.abstraction import ITempyInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class TempyInboxService(ITempyInboxService):
    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        enc = urllib.parse.quote(inbox.address, safe="")
        data = HttpUtility.json("GET", f"{self.API}/mailbox/{enc}/messages")
        items = data.get("messages") if isinstance(data, dict) else None
        if items is None and isinstance(data, list):
            items = data
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        for i, x in enumerate(items):
            if isinstance(x, dict):
                msg = dict(x)
                msg.setdefault("id", str(x.get("id") or i))
                out.append(msg)
        return out

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        return VerifyUtility.blob_from_parts(
            msg.get("subject"),
            msg.get("body"),
            msg.get("body_text"),
            msg.get("html"),
            msg.get("text"),
            msg.get("content"),
        )
