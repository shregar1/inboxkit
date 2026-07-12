from __future__ import annotations

from typing import Any, Type

from inboxkit.errors.provider.abstraction import IProviderError
from inboxkit.errors.provider.tempail import TempailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.tempail._http import TempailHttp, extract_session
from inboxkit.services.providers.tempail.abstraction import ITempailGenerateService
from inboxkit.services.providers.tempail.inbox import TempailInboxService
from inboxkit.utilities import NameUtility


class TempailGenerateService(ITempailGenerateService):
    """Mint via homepage session scrape; destroy via /en/api/yoket/."""

    _error_cls: Type[IProviderError] = TempailError
    _inbox_cls: Type[TempailInboxService] = TempailInboxService

    def _client(self, cookie: str = "") -> TempailHttp:
        return TempailHttp(
            cookie,
            site=self.SITE,
            provider=self.PROVIDER,
            error_cls=self._error_cls,
        )

    def _apis(self, inbox_or_session: TempInbox | dict[str, Any]) -> dict[str, str]:
        if isinstance(inbox_or_session, TempInbox):
            meta = inbox_or_session.meta or {}
            apis = dict(self.DEFAULT_APIS)
            apis.update(meta.get("apis") or {})
            return apis
        apis = dict(self.DEFAULT_APIS)
        apis.update(inbox_or_session.get("apis") or {})
        return apis

    def fetch_session(self) -> dict[str, Any]:
        http = self._client()
        html = http.get(self.HOME)
        session = extract_session(
            html, provider=self.PROVIDER, error_cls=self._error_cls
        )
        email = session.get("email")
        if not email or "@" not in str(email):
            raise self._error_cls(
                f"{self.PROVIDER}: could not extract address from homepage",
                code=f"{self.PROVIDER.replace('.', '_')}_no_email",
            )
        session["cookie"] = http.cookie
        session["email"] = str(email).strip()
        return session

    def destroy_mailbox(self, inbox: TempInbox) -> Any:
        http = self._client((inbox.meta or {}).get("cookie") or "")
        url = self._apis(inbox)["yoket"]
        return http.post_json(url, {"oturum": inbox.token})

    def recover_qr(self, inbox: TempInbox) -> Any:
        apis = self._apis(inbox)
        if "sifre" not in apis:
            raise self._error_cls(
                f"{self.PROVIDER}: recover_qr / sifre API not available",
                code=f"{self.PROVIDER.replace('.', '_')}_no_sifre",
            )
        http = self._client((inbox.meta or {}).get("cookie") or "")
        return http.post_json(apis["sifre"], {"oturum": inbox.token})

    def mint(self) -> TempInbox:
        session = self.fetch_session()
        email = str(session["email"])
        local = email.split("@", 1)[0]
        inbox_svc = self._inbox_cls()
        return TempInbox(
            address=email,
            provider=self.PROVIDER,
            token=str(session["oturum"]),
            meta={
                "oturum": session["oturum"],
                "tarih": session.get("tarih") or "",
                "cookie": session.get("cookie") or "",
                "apis": session.get("apis") or dict(self.DEFAULT_APIS),
                "display_name": NameUtility.realistic_display_name(local),
                "local": local,
                "domain": email.split("@", 1)[-1],
                "ttl_hint_hours": 1,
                "view_hint": f"{self.SITE}/",
                "site": self.SITE,
            },
            _list=inbox_svc.list_messages,
            _read=inbox_svc.read_message,
        )
