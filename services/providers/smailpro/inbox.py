from __future__ import annotations

import os
from typing import Any

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.smailpro import SmailProError
from inboxkit.models import TempInbox
from inboxkit.services.providers.smailpro.abstraction import ISmailProInboxService
from inboxkit.utilities import HttpUtility, VerifyUtility


class SmailProInboxService(ISmailProInboxService):
    """SmailPro inbox / message reads."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = (api_key or os.environ.get("SMAILPRO_API_KEY") or "").strip()

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise UnauthorizedError(
                "smailpro: set SMAILPRO_API_KEY (https://my.sonjj.com) or pass api_key=",
                code="smailpro_missing_api_key",
            )
        return {
            "X-Api-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get(self, path: str, **params: Any) -> Any:
        q = {k: v for k, v in params.items() if v is not None}
        qs = HttpUtility.urlencode({k: str(v) for k, v in q.items()}) if q else ""
        url = f"{self.BASE}{path}" + (f"?{qs}" if qs else "")
        try:
            return HttpUtility.json("GET", url, headers=self._headers())
        except RuntimeError as e:
            raise SmailProError(str(e)) from e

    def _kind(self, inbox: TempInbox) -> str:
        return str((inbox.meta or {}).get("kind") or "email")

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        kind = self._kind(inbox)
        if kind == "gmail":
            data = self._get(
                "/v1/temp_gmail/inbox",
                email=inbox.address,
                timestamp=(inbox.meta or {}).get("timestamp") or 0,
            )
        elif kind == "outlook":
            data = self._get(
                "/v1/temp_outlook/inbox",
                email=inbox.address,
                timestamp=(inbox.meta or {}).get("timestamp") or 0,
            )
        else:
            data = self._get("/v1/temp_email/inbox", email=inbox.address)

        messages = data.get("messages") if isinstance(data, dict) else None
        if not isinstance(messages, list):
            return []
        out: list[dict[str, Any]] = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            msg = dict(m)
            # Normalize id for TempInbox / poll helpers
            msg.setdefault("id", str(m.get("mid") or m.get("id") or ""))
            out.append(msg)
        return out

    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        kind = self._kind(inbox)
        if kind == "gmail":
            path = "/v1/temp_gmail/message"
        elif kind == "outlook":
            path = "/v1/temp_outlook/message"
        else:
            path = "/v1/temp_email/message"
        data = self._get(path, email=inbox.address, mid=message_id)
        if not isinstance(data, dict):
            raise SmailProError(f"smailpro: bad message: {data}")
        return data

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("mid") or msg.get("id") or "")
        base = VerifyUtility.blob_from_parts(
            msg.get("textSubject"), msg.get("subject"), msg.get("textFrom"), msg.get("from")
        )
        if not mid:
            return base
        full = self.get_message(inbox, mid)
        return VerifyUtility.blob_from_parts(base, full.get("body"), full.get("text"), full.get("html"))

    def remove_gmail_message(self, inbox: TempInbox, message_id: str) -> Any:
        if self._kind(inbox) != "gmail":
            raise SmailProError("smailpro: remove_gmail_message only applies to kind=gmail")
        return self._get(
            "/v1/temp_gmail/remove_message",
            email=inbox.address,
            mid=message_id,
        )

    def list_attachments(self, inbox: TempInbox, message_id: str) -> Any:
        if self._kind(inbox) != "email":
            raise SmailProError("smailpro: attachments endpoint is for kind=email only")
        return self._get(
            "/v1/temp_email/attachments",
            email=inbox.address,
            mid=message_id,
        )
