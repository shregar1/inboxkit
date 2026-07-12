"""Shared HTTP + HTML helpers for oturum-session temp-mail sites
(tempail.com, tempmail.net, …).
"""

from __future__ import annotations

import html as html_lib
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Type

from inboxkit.errors.provider.abstraction import IProviderError
from inboxkit.errors.provider.tempail import TempailError

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_CFEMAIL_RE = re.compile(r"data-cfemail=\"([0-9a-fA-F]+)\"")
_OTURUM_RE = re.compile(r'var\s+oturum="([^"]*)"')
_TARIH_RE = re.compile(r'var\s+tarih="([^"]*)"')
_API_RE = re.compile(r'var\s+url_api_(\w+)="([^"]*)"')
_EMAIL_INPUT_RE = re.compile(
    r'id="(?:email_input|eposta_adres)"[^>]*value="([^"]*)"', re.I
)
_MAIL_LI_RE = re.compile(
    r'<li[^>]*\bid="mail_([^"]+)"[^>]*>(.*?)</li>', re.I | re.S
)
_MAIL_OKU_RE = re.compile(
    r"mail_oku\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
)
_SENDER_RE = re.compile(
    r'class="[^"]*gonderen[^"]*"[^>]*>(.*?)</div>', re.I | re.S
)
_SUBJECT_RE = re.compile(
    r'class="[^"]*(?:konu|baslik|subject)[^"]*"[^>]*>(.*?)</div>', re.I | re.S
)
_TIME_RE = re.compile(
    r'class="[^"]*(?:zaman|time|tarih)[^"]*"[^>]*>(.*?)</div>', re.I | re.S
)
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_TARIH_RE = re.compile(r'tarih="(\d+)"')


def decode_cfemail(enc: str) -> str:
    key = int(enc[:2], 16)
    return "".join(
        chr(int(enc[i : i + 2], 16) ^ key) for i in range(2, len(enc), 2)
    )


def strip_tags(blob: str) -> str:
    text = _TAG_RE.sub(" ", blob)
    return html_lib.unescape(re.sub(r"\s+", " ", text)).strip()


def is_challenge(body: str) -> bool:
    low = body.lower()
    return (
        "verifying your request" in low
        or "g-recaptcha" in low
        or "bot-kontrol.php" in low
        or "please verify that you are not a robot" in low
    )


def extract_email(html: str) -> str | None:
    m = _EMAIL_INPUT_RE.search(html)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = _CFEMAIL_RE.search(html)
    if m:
        try:
            return decode_cfemail(m.group(1))
        except Exception:
            return None
    return None


def extract_session(
    html: str,
    *,
    provider: str = "tempail",
    error_cls: Type[IProviderError] = TempailError,
) -> dict[str, Any]:
    if is_challenge(html):
        raise error_cls(
            f"{provider}: bot/captcha challenge — open the site in a browser "
            "or retry later",
            code=f"{provider.replace('.', '_')}_captcha",
        )
    oturum_m = _OTURUM_RE.search(html)
    oturum = oturum_m.group(1) if oturum_m else ""
    tarih_m = _SCRIPT_TARIH_RE.search(html) or _TARIH_RE.search(html)
    tarih = tarih_m.group(1) if tarih_m else ""
    if not oturum:
        raise error_cls(
            f"{provider}: missing oturum session token",
            code=f"{provider.replace('.', '_')}_no_oturum",
        )
    email = extract_email(html)
    apis = dict(_API_RE.findall(html))
    return {
        "oturum": oturum,
        "tarih": tarih,
        "email": email,
        "apis": apis,
        "raw_len": len(html),
    }


def extract_tarih(html: str) -> str | None:
    m = _SCRIPT_TARIH_RE.search(html) or _TARIH_RE.search(html)
    return m.group(1) if m else None


def parse_message_list(
    html: str,
    *,
    provider: str = "tempail",
    error_cls: Type[IProviderError] = TempailError,
) -> list[dict[str, Any]]:
    """Parse kontrol HTML fragment into message dicts."""
    if is_challenge(html):
        raise error_cls(
            f"{provider}: bot/captcha challenge on inbox poll",
            code=f"{provider.replace('.', '_')}_captcha",
        )
    out: list[dict[str, Any]] = []
    for mid, body in _MAIL_LI_RE.findall(html):
        if mid.lower() in {"", "baslik"} or 'class="baslik"' in body[:80]:
            continue
        oku = _MAIL_OKU_RE.search(body)
        dom_id = oku.group(1) if oku else mid
        alt_id = oku.group(2) if oku else mid
        sender_m = _SENDER_RE.search(body)
        subject_m = _SUBJECT_RE.search(body)
        time_m = _TIME_RE.search(body)
        out.append(
            {
                "id": str(dom_id),
                "alt_id": str(alt_id),
                "from": strip_tags(sender_m.group(1)) if sender_m else "",
                "subject": strip_tags(subject_m.group(1)) if subject_m else "",
                "time": strip_tags(time_m.group(1)) if time_m else "",
                "html": body,
            }
        )
    if not out and "<li" in html and "Waiting for emails" not in html:
        items = re.findall(r"<li(?![^>]*baslik)[^>]*>(.*?)</li>", html, re.I | re.S)
        for i, body in enumerate(items):
            if "gonderen" not in body and "Sender" in strip_tags(body):
                continue
            sender_m = _SENDER_RE.search(body)
            subject_m = _SUBJECT_RE.search(body)
            if not sender_m and not subject_m:
                continue
            out.append(
                {
                    "id": str(i),
                    "alt_id": str(i),
                    "from": strip_tags(sender_m.group(1)) if sender_m else "",
                    "subject": strip_tags(subject_m.group(1)) if subject_m else "",
                    "time": "",
                    "html": body,
                }
            )
    return out


def cookie_header_from_jar(jar: http.cookiejar.CookieJar) -> str:
    return "; ".join(f"{c.name}={c.value}" for c in jar)


def jar_from_cookie_header(
    header: str, *, domain: str = "tempail.com"
) -> http.cookiejar.CookieJar:
    jar = http.cookiejar.CookieJar()
    if not header.strip():
        return jar
    from http.cookiejar import Cookie

    for part in header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        jar.set_cookie(
            Cookie(
                version=0,
                name=name.strip(),
                value=value.strip(),
                port=None,
                port_specified=False,
                domain=domain,
                domain_specified=True,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
                rfc2109=False,
            )
        )
    return jar


class TempailHttp:
    """Cookie + form-urlencoded client for oturum-session sites."""

    def __init__(
        self,
        cookie: str | None = None,
        *,
        site: str = "https://tempail.com",
        provider: str = "tempail",
        error_cls: Type[IProviderError] = TempailError,
    ) -> None:
        self.site = site.rstrip("/")
        self.provider = provider
        self.error_cls = error_cls
        host = urllib.parse.urlparse(self.site).hostname or "tempail.com"
        self.jar = jar_from_cookie_header(cookie or "", domain=host)
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    @property
    def cookie(self) -> str:
        return cookie_header_from_jar(self.jar)

    def request(
        self,
        method: str,
        url: str,
        *,
        form: dict[str, Any] | None = None,
        timeout: float = 30,
    ) -> str:
        headers = {
            "User-Agent": _UA,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.site,
            "Referer": f"{self.site}/",
        }
        data = None
        if form is not None:
            pairs: list[tuple[str, str]] = []
            for k, v in form.items():
                if isinstance(v, (list, tuple)):
                    for item in v:
                        pairs.append((f"{k}[]", str(item)))
                else:
                    pairs.append((k, str(v)))
            data = urllib.parse.urlencode(pairs).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["X-Requested-With"] = "XMLHttpRequest"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            # 304 = no inbox change since tarih watermark (empty poll)
            if e.code == 304:
                e.read()  # drain
                return ""
            err = e.read().decode("utf-8", errors="replace")
            raise self.error_cls(
                f"{self.provider}: HTTP {e.code} {url}: {err[:300]}"
            ) from e
        except Exception as e:  # noqa: BLE001
            raise self.error_cls(f"{self.provider}: request failed: {e}") from e

    def get(self, url: str) -> str:
        return self.request("GET", url)

    def post_form(self, url: str, form: dict[str, Any]) -> str:
        return self.request("POST", url, form=form)

    def post_json(self, url: str, form: dict[str, Any]) -> Any:
        raw = self.post_form(url, form)
        if is_challenge(raw):
            raise self.error_cls(
                f"{self.provider}: bot/captcha challenge",
                code=f"{self.provider.replace('.', '_')}_captcha",
            )
        try:
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {"raw": raw}
