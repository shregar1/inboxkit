from __future__ import annotations

from typing import Any

from inboxkit.models import TempInbox
from inboxkit.services.providers.temp_mail_app.abstraction import ITempMailAppInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class TempMailAppInboxService(ITempMailAppInboxService):
    def _headers(self, visitor_id: str) -> dict[str, str]:
        return {
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Referer": f"{self.BASE}/",
            "User-Agent": self.UA,
            "visitor-id": visitor_id,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        qs = HttpUtility.urlencode({"part": "main"})
        try:
            data = HttpUtility.json(
                "GET",
                f"{self.BASE}/api/mail/list?{qs}",
                headers=self._headers(inbox.token),
            )
        except Exception:
            return []
        items = data if isinstance(data, list) else data.get("data") or data.get("list") or []
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        for i, x in enumerate(items):
            if isinstance(x, dict):
                msg = dict(x)
                msg.setdefault("id", str(x.get("id") or x.get("mail_id") or i))
                out.append(msg)
        return out

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        return VerifyUtility.blob_from_parts(
            msg.get("subject"), msg.get("from"), msg.get("text"), msg.get("html"),
            msg.get("body"), msg.get("content"), msg.get("preview"),
        )
