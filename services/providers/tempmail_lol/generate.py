from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.tempmail_lol import TempMailLolError
from inboxkit.models import TempInbox
from inboxkit.services.providers.tempmail_lol.abstraction import ITempMailLolGenerateService
from inboxkit.services.providers.tempmail_lol.inbox import TempMailLolInboxService
from inboxkit.utilities import HttpUtility


class TempMailLolGenerateService(ITempMailLolGenerateService):
    def create_inbox(
        self,
        *,
        prefix: str | None = None,
        domain: str | None = None,
        community: bool | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        # Free path
        if not api_key and not prefix and not domain and community is None:
            data = HttpUtility.json("GET", f"{self.BASE}/generate")
        else:
            body: dict[str, Any] = {}
            if prefix is not None:
                body["prefix"] = prefix
            if domain is not None:
                body["domain"] = domain
            if community is not None:
                body["community"] = community
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = api_key
            # v2 create used by official JS client when options/key present
            data = HttpUtility.json(
                "POST",
                f"{self.BASE}/v2/inbox/create",
                body=body or {},
                headers=headers,
            )
        if not isinstance(data, dict):
            raise TempMailLolError(f"tempmail.lol: bad create: {data}")
        address = (data.get("address") or "").strip()
        token = (data.get("token") or "").strip()
        if not address or not token:
            raise TempMailLolError(f"tempmail.lol: bad response: {data}")
        return data

    def set_webhook(self, url: str, *, api_key: str) -> Any:
        return HttpUtility.json(
            "POST",
            f"{self.BASE}/webhook",
            body={"url": url},
            headers={"Authorization": api_key, "Content-Type": "application/json"},
        )

    def remove_webhook(self, *, api_key: str) -> Any:
        return HttpUtility.json(
            "DELETE",
            f"{self.BASE}/webhook",
            headers={"Authorization": api_key},
        )

    def mint(self) -> TempInbox:
        data = self.create_inbox()
        inbox_svc = TempMailLolInboxService()
        return TempInbox(
            address=str(data["address"]).strip(),
            provider=self.PROVIDER,
            token=str(data["token"]).strip(),
            meta={"raw": data},
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
