from __future__ import annotations

import json
import secrets
from typing import Any

from inboxkit.errors.provider.temp_mail_app import TempMailAppError
from inboxkit.models import TempInbox
from inboxkit.services.providers.temp_mail_app.abstraction import ITempMailAppGenerateService
from inboxkit.services.providers.temp_mail_app.inbox import TempMailAppInboxService
from inboxkit.utilities import HttpUtility


class TempMailAppGenerateService(ITempMailAppGenerateService):
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

    def _new_visitor(self) -> str:
        return (
            f"{secrets.token_hex(4)}-{secrets.token_hex(2)}-"
            f"{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(6)}"
        )

    def create_address(
        self, *, expire_minutes: int = 1440, refresh: bool = True
    ) -> dict[str, Any]:
        visitor_id = self._new_visitor()
        qs = HttpUtility.urlencode(
            {
                "refresh": "true" if refresh else "false",
                "expire": str(expire_minutes),
                "part": "main",
            }
        )
        raw = HttpUtility.text(
            "GET", f"{self.BASE}/api/mail/address?{qs}", headers=self._headers(visitor_id)
        )
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as e:
            raise TempMailAppError(f"temp-mail.app: bad json: {raw[:200]}") from e
        email = ""
        if isinstance(data, dict):
            email = (
                data.get("email")
                or data.get("address")
                or (data.get("data") or {}).get("email")
                or (data.get("data") or {}).get("address")
                or ""
            )
            if isinstance(email, dict):
                email = email.get("email") or email.get("address") or ""
        email = str(email).strip()
        if not email or "@" not in email:
            raise TempMailAppError(f"temp-mail.app: no address in {data}")
        return {"email": email, "visitor_id": visitor_id, "raw": data}

    def mint(self) -> TempInbox:
        created = self.create_address()
        inbox_svc = TempMailAppInboxService()
        return TempInbox(
            address=created["email"],
            provider=self.PROVIDER,
            token=created["visitor_id"],
            meta={"visitor_id": created["visitor_id"], "raw": created.get("raw")},
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
