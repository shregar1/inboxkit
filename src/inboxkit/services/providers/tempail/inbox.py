from __future__ import annotations

from typing import Any, Type

from inboxkit.errors.provider.abstraction import IProviderError
from inboxkit.errors.provider.tempail import TempailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.tempail._http import (
    TempailHttp,
    extract_tarih,
    is_challenge,
    parse_message_list,
    strip_tags,
)
from inboxkit.services.providers.tempail.abstraction import ITempailInboxService
from inboxkit.utilities import VerifyUtility


class TempailInboxService(ITempailInboxService):
    """Inbox ops via kontrol / oku / sil / duzelt HTML form posts."""

    _error_cls: Type[IProviderError] = TempailError

    def _client(self, cookie: str = "") -> TempailHttp:
        return TempailHttp(
            cookie,
            site=self.SITE,
            provider=self.PROVIDER,
            error_cls=self._error_cls,
        )

    def _apis(self, inbox: TempInbox) -> dict[str, str]:
        apis = dict(self.DEFAULT_APIS)
        apis.update((inbox.meta or {}).get("apis") or {})
        return apis

    def _http(self, inbox: TempInbox) -> TempailHttp:
        return self._client((inbox.meta or {}).get("cookie") or "")

    def _oturum(self, inbox: TempInbox) -> str:
        return str(inbox.token or (inbox.meta or {}).get("oturum") or "")

    def _tarih(self, inbox: TempInbox) -> str:
        return str((inbox.meta or {}).get("tarih") or "")

    def _persist_cookie(self, inbox: TempInbox, http: TempailHttp) -> None:
        if inbox.meta is None:
            inbox.meta = {}
        inbox.meta["cookie"] = http.cookie

    def poll_inbox(self, inbox: TempInbox) -> str:
        http = self._http(inbox)
        form = {
            "oturum": self._oturum(inbox),
            "tarih": self._tarih(inbox),
            "geri_don": f"{self.SITE}/",
            "email": inbox.address,
        }
        raw = http.post_form(self._apis(inbox)["kontrol"], form)
        if is_challenge(raw):
            raise self._error_cls(
                f"{self.PROVIDER}: bot/captcha challenge on inbox poll",
                code=f"{self.PROVIDER.replace('.', '_')}_captcha",
            )
        self._persist_cookie(inbox, http)
        yeni = extract_tarih(raw)
        if yeni and inbox.meta is not None:
            inbox.meta["tarih"] = yeni
        return raw

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        return parse_message_list(
            self.poll_inbox(inbox),
            provider=self.PROVIDER,
            error_cls=self._error_cls,
        )

    def get_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> str:
        http = self._http(inbox)
        a = alt_id if alt_id is not None else message_id
        e = message_id
        raw = http.post_form(
            self._apis(inbox)["oku"],
            {"oturum": self._oturum(inbox), "veri": [a, e]},
        )
        if is_challenge(raw):
            raise self._error_cls(
                f"{self.PROVIDER}: bot/captcha challenge on read",
                code=f"{self.PROVIDER.replace('.', '_')}_captcha",
            )
        self._persist_cookie(inbox, http)
        return raw

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        mid = str(msg.get("id") or "")
        alt = str(msg.get("alt_id") or mid)
        base = VerifyUtility.blob_from_parts(
            msg.get("subject"),
            msg.get("from"),
            msg.get("time"),
            strip_tags(str(msg.get("html") or "")),
        )
        if not mid:
            return base
        try:
            full_html = self.get_message(inbox, mid, alt_id=alt)
        except Exception:
            return base
        return VerifyUtility.blob_from_parts(base, strip_tags(full_html), full_html)

    def delete_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> None:
        http = self._http(inbox)
        e = alt_id if alt_id is not None else message_id
        a = message_id
        http.post_form(
            self._apis(inbox)["sil"],
            {"oturum": self._oturum(inbox), "veri": [e, a]},
        )
        self._persist_cookie(inbox, http)

    def mark_message(
        self, inbox: TempInbox, message_id: str, *, alt_id: str | None = None
    ) -> None:
        http = self._http(inbox)
        e = alt_id if alt_id is not None else message_id
        a = message_id
        http.post_form(
            self._apis(inbox)["duzelt"],
            {"oturum": self._oturum(inbox), "veri": [e, a]},
        )
        self._persist_cookie(inbox, http)
