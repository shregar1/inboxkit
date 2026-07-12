from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.tempy import TempyError
from inboxkit.models import TempInbox
from inboxkit.services.providers.tempy.abstraction import ITempyGenerateService
from inboxkit.services.providers.tempy.inbox import TempyInboxService
from inboxkit.utilities import HttpUtility


class TempyGenerateService(ITempyGenerateService):
    def create_mailbox(
        self,
        *,
        domain: str | None = None,
        webhook_url: str | None = None,
        webhook_format: str = "json",
        api_key: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if domain:
            body["domain"] = domain
        if webhook_url:
            body["webhookUrl"] = webhook_url
            body["webhookFormat"] = webhook_format
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Api-Key"] = api_key
        data = HttpUtility.json("POST", f"{self.API}/mailbox", body=body or {}, headers=headers)
        if not isinstance(data, dict) or not (data.get("email") or data.get("address")):
            raise TempyError(f"tempy.email: bad create: {data}")
        return data

    def get_mailbox(self, address: str) -> dict[str, Any]:
        import urllib.parse
        enc = urllib.parse.quote(address, safe="")
        data = HttpUtility.json("GET", f"{self.API}/mailbox/{enc}")
        if not isinstance(data, dict):
            raise TempyError(f"tempy.email: bad status: {data}")
        return data

    def delete_mailbox(self, address: str) -> None:
        import urllib.parse
        enc = urllib.parse.quote(address, safe="")
        HttpUtility.json("DELETE", f"{self.API}/mailbox/{enc}")

    def mint(self) -> TempInbox:
        data = self.create_mailbox()
        email = (data.get("email") or data.get("address") or "").strip()
        if not email:
            raise TempyError(f"tempy.email: bad response: {data}")
        inbox_svc = TempyInboxService()
        return TempInbox(
            address=email,
            provider=self.PROVIDER,
            token=email,
            meta={
                "expires_at": data.get("expiresAt") or data.get("expires_at"),
                "seconds_remaining": data.get("secondsRemaining"),
                "web_url": data.get("webUrl"),
                "raw": data,
            },
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
