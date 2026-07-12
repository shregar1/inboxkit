from __future__ import annotations

import os
import time
from typing import Any, Literal

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.smailpro import SmailProError
from inboxkit.models import TempInbox
from inboxkit.services.providers.smailpro.abstraction import (
    ISmailProGenerateService,
    MailKind,
)
from inboxkit.services.providers.smailpro.inbox import SmailProInboxService
from inboxkit.utilities import HttpUtility, NameUtility


class SmailProGenerateService(ISmailProGenerateService):
    """SmailPro account minting (Sonjj REST API)."""

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

    def list_domains(self) -> list[str]:
        data = self._get("/v1/temp_email/domains")
        domains = data.get("domains") if isinstance(data, dict) else None
        if not isinstance(domains, list):
            raise SmailProError(f"smailpro: bad domains: {data}")
        return [str(d) for d in domains]

    def create_email(self, email: str, *, expiry_minutes: int = 0) -> dict[str, Any]:
        data = self._get(
            "/v1/temp_email/create",
            email=email,
            expiry_minutes=int(expiry_minutes),
        )
        return data if isinstance(data, dict) else {"email": email, "raw": data}

    def random_gmail(
        self, *, type: Literal["real", "alias"] = "alias", password: str | None = None
    ) -> dict[str, Any]:
        data = self._get("/v1/temp_gmail/random", type=type, password=password)
        if not isinstance(data, dict) or not data.get("email"):
            raise SmailProError(f"smailpro: bad gmail random: {data}")
        return data

    def list_gmail(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        type: Literal["real", "alias"] = "alias",
        password: str | None = None,
    ) -> dict[str, Any]:
        data = self._get(
            "/v1/temp_gmail/list",
            page=page,
            limit=limit,
            type=type,
            password=password,
        )
        if not isinstance(data, dict):
            raise SmailProError(f"smailpro: bad gmail list: {data}")
        return data

    def random_outlook(
        self, *, type: Literal["real", "alias"] = "alias", password: str | None = None
    ) -> dict[str, Any]:
        data = self._get("/v1/temp_outlook/random", type=type, password=password)
        if not isinstance(data, dict) or not data.get("email"):
            raise SmailProError(f"smailpro: bad outlook random: {data}")
        return data

    def list_outlook(
        self,
        *,
        page: int = 1,
        limit: int = 10,
        type: Literal["real", "alias"] = "alias",
        password: str | None = None,
    ) -> dict[str, Any]:
        data = self._get(
            "/v1/temp_outlook/list",
            page=page,
            limit=limit,
            type=type,
            password=password,
        )
        if not isinstance(data, dict):
            raise SmailProError(f"smailpro: bad outlook list: {data}")
        return data

    def mint(
        self,
        *,
        kind: MailKind = "email",
        domain: str | None = None,
        email: str | None = None,
        expiry_minutes: int = 0,
        gmail_type: Literal["real", "alias"] = "alias",
    ) -> TempInbox:
        inbox_svc = SmailProInboxService(api_key=self._api_key)
        ts = int(time.time())

        if kind == "gmail":
            data = self.random_gmail(type=gmail_type)
            address = str(data["email"]).strip()
            timestamp = int(data.get("timestamp") or ts)
            return TempInbox(
                address=address,
                provider=self.PROVIDER,
                token=address,
                meta={
                    "kind": "gmail",
                    "timestamp": timestamp,
                    "type": data.get("type") or gmail_type,
                    "raw": data,
                },
                _list=inbox_svc.list_messages,
                _read=inbox_svc.read_message,
            )

        if kind == "outlook":
            data = self.random_outlook(type=gmail_type)
            address = str(data["email"]).strip()
            timestamp = int(data.get("timestamp") or ts)
            return TempInbox(
                address=address,
                provider=self.PROVIDER,
                token=address,
                meta={
                    "kind": "outlook",
                    "timestamp": timestamp,
                    "type": data.get("type") or gmail_type,
                    "raw": data,
                },
                _list=inbox_svc.list_messages,
                _read=inbox_svc.read_message,
            )

        # Default: custom-domain temp_email
        if not email:
            domains = self.list_domains()
            if not domains:
                raise SmailProError("smailpro: no domains")
            host = domain or domains[0]
            local = NameUtility.realistic_local().replace(".", "")
            email = f"{local}@{host}"
        self.create_email(email, expiry_minutes=expiry_minutes)
        return TempInbox(
            address=email,
            provider=self.PROVIDER,
            token=email,
            meta={"kind": "email", "timestamp": ts, "expiry_minutes": expiry_minutes},
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
