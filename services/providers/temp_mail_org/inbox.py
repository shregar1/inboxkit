from __future__ import annotations

import os
import urllib.parse
from typing import Any

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.temp_mail_org import TempMailOrgError
from inboxkit.models import TempInbox
from inboxkit.services.providers.temp_mail_org.abstraction import ITempMailOrgInboxService
from inboxkit.utilities import HttpUtility, VerifyUtility


class TempMailOrgInboxService(ITempMailOrgInboxService):
    """temp-mail.org message ops — web token or official X-API-Key."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = (
            api_key
            or os.environ.get("TEMP_MAIL_API_KEY")
            or os.environ.get("TEMPMAIL_IO_API_KEY")
            or ""
        ).strip()

    def _backend(self, inbox: TempInbox) -> str:
        return str((inbox.meta or {}).get("backend") or ("official" if self._api_key else "web"))

    def _require_key(self) -> str:
        if not self._api_key:
            raise UnauthorizedError(
                "temp-mail.org: set TEMP_MAIL_API_KEY for official message APIs",
                code="temp_mail_missing_api_key",
            )
        return self._api_key

    def _web(self, method: str, path: str, *, body: dict | None = None, token: str | None = None) -> Any:
        headers = dict(self.HEADERS)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            return HttpUtility.json(
                method, f"{self.BASE}{path}", body=body, headers=headers, token=None
            )
        except RuntimeError as e:
            raise TempMailOrgError(str(e)) from e

    def _official(self, method: str, path: str, *, body: dict | None = None) -> Any:
        key = self._require_key()
        try:
            return HttpUtility.json(
                method,
                f"{self.OFFICIAL_BASE}{path}",
                body=body,
                headers={"X-API-Key": key, "Content-Type": "application/json"},
            )
        except RuntimeError as e:
            raise TempMailOrgError(str(e)) from e

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        if self._backend(inbox) == "official":
            enc = urllib.parse.quote(inbox.address, safe="")
            data = self._official("GET", f"/emails/{enc}/messages")
            if isinstance(data, dict):
                items = data.get("messages") or data.get("data") or []
            elif isinstance(data, list):
                items = data
            else:
                items = []
            return [x for x in items if isinstance(x, dict)]

        data = self._web("GET", f"/email/{inbox.address}/messages", token=inbox.token)
        if isinstance(data, list):
            out: list[dict[str, Any]] = []
            for i, x in enumerate(data):
                if isinstance(x, dict):
                    msg = dict(x)
                    msg.setdefault("id", str(x.get("id") or x.get("_id") or i))
                    out.append(msg)
            return out
        if isinstance(data, dict):
            items = data.get("messages") or data.get("mail") or data.get("data") or []
            if isinstance(items, list):
                return [x for x in items if isinstance(x, dict)]
        return []

    def get_message(self, inbox: TempInbox, message_id: str) -> dict[str, Any]:
        if self._backend(inbox) == "official":
            data = self._official("GET", f"/messages/{message_id}")
            if not isinstance(data, dict):
                raise TempMailOrgError(f"temp-mail.io: bad message: {data}")
            return data
        for msg in self.list_messages(inbox):
            if str(msg.get("id")) == str(message_id):
                return msg
        raise TempMailOrgError(f"temp-mail.org: message not found: {message_id}")

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("id") or "")
        base = VerifyUtility.blob_from_parts(
            msg.get("subject"),
            msg.get("from"),
            msg.get("body_text"),
            msg.get("body_html"),
            msg.get("text"),
            msg.get("html"),
            msg.get("body"),
            msg.get("preview"),
        )
        if self._backend(inbox) == "official" and mid:
            try:
                full = self.get_message(inbox, mid)
            except Exception:
                return base
            return VerifyUtility.blob_from_parts(
                base,
                full.get("subject"),
                full.get("from"),
                full.get("body_text"),
                full.get("body_html"),
            )
        return base

    def delete_message(self, inbox: TempInbox, message_id: str) -> None:
        self._official("DELETE", f"/messages/{message_id}")

    def get_source(self, inbox: TempInbox, message_id: str) -> Any:
        return self._official("GET", f"/messages/{message_id}/source")

    def download_attachment(
        self, inbox: TempInbox, message_id: str, attachment_id: str
    ) -> bytes:
        key = self._require_key()
        return HttpUtility.bytes(
            "GET",
            f"{self.OFFICIAL_BASE}/messages/{message_id}/attachments/{attachment_id}",
            headers={"X-API-Key": key},
        )
