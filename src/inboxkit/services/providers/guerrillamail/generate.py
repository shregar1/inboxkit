from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.guerrillamail import GuerrillaMailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.guerrillamail.abstraction import IGuerrillaMailGenerateService
from inboxkit.services.providers.guerrillamail.inbox import GuerrillaMailInboxService
from inboxkit.utilities import HttpUtility, NameUtility


class GuerrillaMailGenerateService(IGuerrillaMailGenerateService):
    def _call(self, f: str, **params: Any) -> Any:
        q = {"f": f, "ip": "127.0.0.1", "agent": "inboxkit", **params}
        return HttpUtility.json("GET", f"{self.BASE}?{HttpUtility.urlencode({k: str(v) for k, v in q.items()})}")

    def get_email_address(self, *, lang: str = "en") -> dict[str, Any]:
        data = self._call("get_email_address", lang=lang)
        if not isinstance(data, dict) or not data.get("sid_token"):
            raise GuerrillaMailError(f"guerrillamail: bad get_email_address: {data}")
        return data

    def set_email_user(self, sid_token: str, email_user: str, *, lang: str = "en") -> dict[str, Any]:
        data = self._call("set_email_user", sid_token=sid_token, email_user=email_user, lang=lang)
        if not isinstance(data, dict):
            raise GuerrillaMailError(f"guerrillamail: bad set_email_user: {data}")
        return data

    def forget_me(self, inbox: TempInbox) -> Any:
        return self._call("forget_me", email_addr=inbox.address, sid_token=inbox.token)

    def extend(self, inbox: TempInbox) -> dict[str, Any]:
        data = self._call("extend", sid_token=inbox.token)
        if not isinstance(data, dict):
            raise GuerrillaMailError(f"guerrillamail: bad extend: {data}")
        return data

    def mint(self) -> TempInbox:
        data = self.get_email_address()
        sid = str(data.get("sid_token") or "").strip()
        local = NameUtility.realistic_local()
        user = local.replace(".", "")
        set_data = self.set_email_user(sid, user)
        email = (set_data.get("email_addr") or data.get("email_addr") or "").strip()
        sid = str(set_data.get("sid_token") or sid).strip()
        if not email:
            raise GuerrillaMailError(f"guerrillamail: set_email_user failed: {set_data}")
        inbox_svc = GuerrillaMailInboxService()
        return TempInbox(
            address=email,
            provider=self.PROVIDER,
            token=sid,
            meta={
                "sid_token": sid,
                "display_name": NameUtility.realistic_display_name(local),
                "local": user,
                "email_timestamp": set_data.get("email_timestamp") or data.get("email_timestamp"),
            },
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
