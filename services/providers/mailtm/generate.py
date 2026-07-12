from __future__ import annotations

from typing import Any

from inboxkit.errors.provider.mailtm import MailTmError
from inboxkit.models import TempInbox
from inboxkit.services.providers.mailtm.abstraction import IMailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
from inboxkit.utilities import HttpUtility, NameUtility


class MailTmGenerateService(IMailTmGenerateService):
    """mail.tm domains + accounts + token (public API)."""

    def list_domains(self, *, page: int = 1) -> list[dict[str, Any]]:
        data = HttpUtility.json("GET", f"{self.BASE}/domains?page={page}")
        return self._members(data)

    def get_domain(self, domain_id: str) -> dict[str, Any]:
        data = HttpUtility.json("GET", f"{self.BASE}/domains/{domain_id}")
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad domain: {data}")
        return data

    def create_account(self, address: str, password: str) -> dict[str, Any]:
        data = HttpUtility.json(
            "POST",
            f"{self.BASE}/accounts",
            body={"address": address, "password": password},
        )
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad account create: {data}")
        return data

    def get_token(self, address: str, password: str) -> str:
        tok = HttpUtility.json(
            "POST",
            f"{self.BASE}/token",
            body={"address": address, "password": password},
        )
        token = tok.get("token") if isinstance(tok, dict) else None
        if not token:
            raise MailTmError(f"mail.tm: no token: {tok}")
        return str(token)

    def get_account(self, inbox: TempInbox, account_id: str) -> dict[str, Any]:
        data = HttpUtility.json("GET", f"{self.BASE}/accounts/{account_id}", token=inbox.token)
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad account: {data}")
        return data

    def delete_account(self, inbox: TempInbox, account_id: str | None = None) -> None:
        aid = account_id or str((inbox.meta or {}).get("account_id") or "")
        if not aid:
            me = self.me(inbox)
            aid = str(me.get("id") or "")
        if not aid:
            raise MailTmError("mail.tm: account id required for delete")
        HttpUtility.json("DELETE", f"{self.BASE}/accounts/{aid}", token=inbox.token)

    def me(self, inbox: TempInbox) -> dict[str, Any]:
        data = HttpUtility.json("GET", f"{self.BASE}/me", token=inbox.token)
        if not isinstance(data, dict):
            raise MailTmError(f"mail.tm: bad /me: {data}")
        return data

    def mint(self) -> TempInbox:
        items = self.list_domains()
        if not items:
            raise MailTmError("mail.tm: no domains")
        active = [
            d for d in items
            if isinstance(d, dict) and d.get("isActive", d.get("is_active", True))
        ]
        pool = active or [d for d in items if isinstance(d, dict)]
        if not pool:
            raise MailTmError("mail.tm: no domains")
        domain = pool[0].get("domain") or pool[0].get("name")
        if not domain:
            raise MailTmError(f"mail.tm: bad domain: {pool[0]!r}")

        inbox_svc = MailTmInboxService()
        last_err: Exception | None = None
        for _ in range(6):
            local = NameUtility.realistic_local()
            address = f"{local}@{domain}"
            password = "Tm!" + NameUtility.random_local(12)
            display = NameUtility.realistic_display_name(local)
            try:
                account = self.create_account(address, password)
                token = self.get_token(address, password)
                return TempInbox(
                    address=address,
                    provider=self.PROVIDER,
                    token=token,
                    meta={
                        "password": password,
                        "display_name": display,
                        "local": local,
                        "token": token,
                        "account_id": account.get("id"),
                    },
                    _list=inbox_svc.list_messages,
                    _read=inbox_svc.read_message,
                )
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if "already used" in msg or "422" in msg:
                    continue
                if isinstance(e, MailTmError):
                    raise
                raise MailTmError(str(e)) from e
        raise MailTmError(f"mail.tm: could not mint address: {last_err}")

    @staticmethod
    def _members(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            items = data.get("hydra:member") or data.get("member") or []
            return [x for x in items if isinstance(x, dict)]
        return []
