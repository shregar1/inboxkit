from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Any

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.temp_mail_org import TempMailOrgError
from inboxkit.models import TempInbox
from inboxkit.services.providers.temp_mail_org.abstraction import (
    Backend,
    ITempMailOrgGenerateService,
)
from inboxkit.services.providers.temp_mail_org.inbox import TempMailOrgInboxService
from inboxkit.utilities import HttpUtility, NameUtility


class TempMailOrgGenerateService(ITempMailOrgGenerateService):
    """temp-mail.org mint — web (free) or official API (TEMP_MAIL_API_KEY)."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = (
            api_key
            or os.environ.get("TEMP_MAIL_API_KEY")
            or os.environ.get("TEMPMAIL_IO_API_KEY")
            or ""
        ).strip()

    def _resolve_backend(self, backend: Backend | None) -> Backend:
        if backend is not None:
            return backend
        return "official" if self._api_key else "web"

    def _require_key(self) -> str:
        if not self._api_key:
            raise UnauthorizedError(
                "temp-mail.org: set TEMP_MAIL_API_KEY (https://temp-mail.io) "
                "for official API, or use backend='web'",
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

    def list_domains(self, *, backend: Backend | None = None) -> list[str]:
        mode = self._resolve_backend(backend)
        if mode == "official":
            data = self._official("GET", "/domains")
            # Official responses vary: list or {domains: [...]}
            if isinstance(data, list):
                return [str(d.get("name") if isinstance(d, dict) else d) for d in data]
            if isinstance(data, dict):
                domains = data.get("domains") or data.get("data") or []
                if isinstance(domains, list):
                    out: list[str] = []
                    for d in domains:
                        if isinstance(d, dict):
                            name = d.get("name") or d.get("domain")
                            if name:
                                out.append(str(name))
                        else:
                            out.append(str(d))
                    return out
            raise TempMailOrgError(f"temp-mail.io: bad domains: {data}")

        payload = self._web("GET", "/domains")
        domains = payload.get("domains") if isinstance(payload, dict) else None
        if not isinstance(domains, list):
            raise TempMailOrgError("temp-mail.org: no domains")
        names = [
            d.get("name")
            for d in domains
            if isinstance(d, dict) and d.get("name") and d.get("type", "public") == "public"
        ]
        if not names:
            names = [d.get("name") for d in domains if isinstance(d, dict) and d.get("name")]
        return [str(n) for n in names if n]

    def create_email(
        self,
        *,
        name: str | None = None,
        domain: str | None = None,
        domain_type: str | None = None,
        backend: Backend | None = None,
        **body: Any,
    ) -> dict[str, Any]:
        mode = self._resolve_backend(backend)
        if mode == "official":
            payload = dict(body)
            if name:
                payload.setdefault("name", name)
            if domain:
                payload.setdefault("domain", domain)
            if domain_type:
                payload.setdefault("domain_type", domain_type)
            data = self._official("POST", "/emails", body=payload or None)
            if not isinstance(data, dict) or not data.get("email"):
                raise TempMailOrgError(f"temp-mail.io: bad create: {data}")
            return data

        local = name or NameUtility.realistic_local()
        if not domain:
            public = self.list_domains(backend="web")
            if not public:
                raise TempMailOrgError("temp-mail.org: no domains")
            domain = secrets.choice(public)
        created = self._web("POST", "/email/new", body={"name": local, "domain": domain})
        if not isinstance(created, dict):
            raise TempMailOrgError(f"temp-mail.org: bad create: {created}")
        return created

    def delete_email(self, inbox: TempInbox) -> None:
        # Official only
        enc = urllib.parse.quote(inbox.address, safe="")
        self._official("DELETE", f"/emails/{enc}")

    def rate_limit(self) -> Any:
        return self._official("GET", "/rate_limit")

    # Back-compat aliases
    def official_list_domains(self, api_key: str | None = None) -> Any:
        if api_key:
            self._api_key = api_key
        return self.list_domains(backend="official")

    def official_create_email(self, api_key: str | None = None, **body: Any) -> dict[str, Any]:
        if api_key:
            self._api_key = api_key
        return self.create_email(backend="official", **body)

    def mint(self, *, backend: Backend | None = None, domain: str | None = None) -> TempInbox:
        mode = self._resolve_backend(backend)
        inbox_svc = TempMailOrgInboxService(api_key=self._api_key)

        if mode == "official":
            created = self.create_email(domain=domain, backend="official")
            email = str(created.get("email") or "").strip()
            if not email:
                raise TempMailOrgError(f"temp-mail.io: bad mint: {created}")
            return TempInbox(
                address=email,
                provider=self.PROVIDER,
                token=self._api_key,  # official auth is API key
                meta={
                    "backend": "official",
                    "ttl": created.get("ttl"),
                    "domain": email.split("@", 1)[-1],
                    "raw": created,
                    "view_hint": f"{self.SITE}/en/",
                },
                _list=inbox_svc.list_messages,
                _read=inbox_svc.read_message,
            )

        last_err: Exception | None = None
        for _ in range(6):
            local = NameUtility.realistic_local()
            display = NameUtility.realistic_display_name(local)
            try:
                created = self.create_email(name=local, domain=domain, backend="web")
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if "422" in msg or "already" in msg or "exist" in msg:
                    continue
                if isinstance(e, TempMailOrgError):
                    raise
                raise TempMailOrgError(str(e)) from e
            email = (created.get("email") or "").strip()
            token = (created.get("token") or "").strip()
            if not email or not token:
                raise TempMailOrgError(f"temp-mail.org: bad create response: {created}")
            return TempInbox(
                address=email,
                provider=self.PROVIDER,
                token=token,
                meta={
                    "backend": "web",
                    "display_name": display,
                    "local": local,
                    "domain": email.split("@", 1)[-1],
                    "view_hint": f"{self.SITE}/en/",
                },
                _list=inbox_svc.list_messages,
                _read=inbox_svc.read_message,
            )
        raise TempMailOrgError(f"temp-mail.org: could not mint address: {last_err}")
