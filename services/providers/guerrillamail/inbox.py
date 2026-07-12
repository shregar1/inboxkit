from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.guerrillamail import GuerrillaMailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.guerrillamail.abstraction import IGuerrillaMailInboxService
from inboxkit.utilities import VerifyUtility, HttpUtility


class GuerrillaMailInboxService(IGuerrillaMailInboxService):
    def _call(self, f: str, **params: Any) -> Any:
        q = {"f": f, "ip": "127.0.0.1", "agent": "inboxkit", **params}
        # del_email needs repeated email_ids[] — handled separately
        return HttpUtility.json("GET", f"{self.BASE}?{HttpUtility.urlencode({k: str(v) for k, v in q.items()})}")

    def check_email(self, inbox: TempInbox, *, seq: int = 0) -> dict[str, Any]:
        data = self._call("check_email", seq=seq, sid_token=inbox.token)
        return data if isinstance(data, dict) else {}

    def get_email_list(self, inbox: TempInbox, *, offset: int = 0) -> dict[str, Any]:
        data = self._call("get_email_list", offset=offset, sid_token=inbox.token)
        return data if isinstance(data, dict) else {}

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        data = self.check_email(inbox, seq=0)
        items = data.get("list") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return []
        return [x for x in items if isinstance(x, dict)]

    def fetch_email(self, inbox: TempInbox, email_id: str) -> dict[str, Any]:
        data = self._call("fetch_email", email_id=email_id, sid_token=inbox.token)
        if not isinstance(data, dict):
            raise GuerrillaMailError(f"guerrillamail: bad fetch_email: {data}")
        return data

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("mail_id") or msg.get("id") or "")
        excerpt = VerifyUtility.blob_from_parts(msg.get("mail_subject"), msg.get("mail_excerpt"), msg.get("subject"))
        if not mid:
            return excerpt
        try:
            full = self.fetch_email(inbox, mid)
        except Exception:
            return excerpt
        return VerifyUtility.blob_from_parts(
            excerpt,
            full.get("mail_subject"),
            full.get("mail_body"),
            full.get("mail_excerpt"),
            full.get("body"),
            full.get("html"),
        )

    def delete_messages(self, inbox: TempInbox, email_ids: list[str | int]) -> list[Any]:
        parts = [f"f=del_email", f"sid_token={inbox.token}", "ip=127.0.0.1", "agent=inboxkit"]
        for eid in email_ids:
            parts.append(f"email_ids[]={eid}")
        data = HttpUtility.json("GET", f"{self.BASE}?{'&'.join(parts)}")
        return data if isinstance(data, list) else [data]
