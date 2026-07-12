"""Utility classes implementing IUtility."""

from __future__ import annotations

import json
import re
import secrets
import string
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from inboxkit.abstractions import IUtility

_UA = "inboxkit/0.1"
_FIRST = (
    "james", "emma", "liam", "olivia", "noah", "ava", "william", "sophia",
    "benjamin", "isabella", "lucas", "mia", "henry", "charlotte", "alexander",
    "amelia", "michael", "harper", "daniel", "evelyn", "matthew", "abigail",
    "samuel", "emily", "david", "elizabeth", "joseph", "sofia", "thomas",
    "grace", "charles", "chloe", "christopher", "victoria", "andrew", "luna",
    "joshua", "hannah", "nathan", "zoe", "ryan", "penelope", "jason", "layla",
    "kevin", "riley", "brian", "nora", "justin", "lily", "brandon", "aurora",
)
_LAST = (
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
    "davis", "rodriguez", "martinez", "hernandez", "lopez", "wilson",
    "anderson", "thomas", "taylor", "moore", "jackson", "martin", "lee",
    "perez", "thompson", "white", "harris", "sanchez", "clark", "ramirez",
    "lewis", "robinson", "walker", "young", "allen", "king", "wright",
    "scott", "torres", "nguyen", "hill", "flores", "green", "adams",
    "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter",
    "roberts", "gomez", "phillips", "evans", "turner", "diaz", "parker",
)
_PASSWORD_SPECIAL = "!@#$%&*"
# Prefer explicit verify-email style URLs, then any https link containing a token=.
_LINK_RE = re.compile(
    r"https?://[^\s\"'<>]+(?:verify[^\s\"'<>]*)?\?[^\"'<>\s]*token=([A-Za-z0-9._~\-%=]+)",
    re.I,
)
_HREF_RE = re.compile(
    r"""href=["'](https?://[^"']+)["']""",
    re.I,
)
_TOKEN_RE = re.compile(r"[?&]token=([A-Za-z0-9._~\-%=]+)", re.I)


class HttpUtility(IUtility):
    @staticmethod
    def json(
        method: str,
        url: str,
        *,
        body: dict | list | str | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        timeout: float = 20,
        content_type: str | None = None,
    ) -> Any:
        hdrs = {"Accept": "application/json", "User-Agent": _UA}
        if headers:
            hdrs.update(headers)
        data = None
        if body is not None:
            if isinstance(body, (dict, list)):
                data = json.dumps(body).encode()
                hdrs.setdefault("Content-Type", content_type or "application/json")
            else:
                data = str(body).encode()
                if content_type:
                    hdrs.setdefault("Content-Type", content_type)
        elif method.upper() in {"POST", "PUT", "PATCH"}:
            # Some APIs require a body even when empty.
            data = b""
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} {url}: {err_body[:300]}") from e

    @staticmethod
    def text(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30,
        body: bytes | None = None,
    ) -> str:
        hdrs = {"User-Agent": _UA, "Accept": "*/*"}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @staticmethod
    def bytes(
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        timeout: float = 60,
    ) -> bytes:
        hdrs = {"User-Agent": _UA, "Accept": "*/*"}
        if headers:
            hdrs.update(headers)
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=hdrs, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()

    @staticmethod
    def urlencode(params: dict[str, str]) -> str:
        return urllib.parse.urlencode(params)


class NameUtility(IUtility):
    @staticmethod
    def random_local(n: int = 10) -> str:
        return "ik" + secrets.token_hex(n // 2 + 1)[:n]

    @staticmethod
    def realistic_local() -> str:
        first = secrets.choice(_FIRST)
        last = secrets.choice(_LAST)
        local = f"{first}.{last}"
        if secrets.randbelow(100) < 35:
            local = f"{local}{secrets.randbelow(90) + 10}"
        return local

    @staticmethod
    def realistic_display_name(local: str | None = None) -> str:
        if local and "." in local:
            base = local.split("@", 1)[0]
            parts = base.rstrip("0123456789").split(".")
            if len(parts) >= 2 and all(p.isalpha() for p in parts[:2]):
                return f"{parts[0].capitalize()} {parts[1].capitalize()}"
        return f"{secrets.choice(_FIRST).capitalize()} {secrets.choice(_LAST).capitalize()}"


class PasswordUtility(IUtility):
    @staticmethod
    def strong(length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + _PASSWORD_SPECIAL
        while True:
            pw = "".join(secrets.choice(alphabet) for _ in range(length))
            if (
                any(c.isupper() for c in pw)
                and any(c.islower() for c in pw)
                and any(c.isdigit() for c in pw)
                and any(c in _PASSWORD_SPECIAL for c in pw)
            ):
                return pw


class VerifyUtility(IUtility):
    @staticmethod
    def extract_link(blob: str) -> str | None:
        """Extract a likely email-verification URL from a message body."""
        text = (blob or "").replace("&amp;", "&")
        m = _LINK_RE.search(text)
        if m:
            # Return the full matched URL (group 0), not just the token
            return m.group(0).rstrip(").,;]>\"'")
        for href in _HREF_RE.findall(text):
            if "token=" in href.lower() or "verify" in href.lower():
                return href.replace("&amp;", "&")
        if "verify" in text.lower():
            tm = _TOKEN_RE.search(text)
            if tm:
                # Best-effort: nearest surrounding URL if present
                near = _LINK_RE.search(text[max(0, tm.start() - 200) : tm.end() + 50])
                if near:
                    return near.group(0).rstrip(").,;]>\"'")
        return None

    @staticmethod
    def blob_from_parts(*parts: Any) -> str:
        chunks: list[str] = []
        for p in parts:
            if p is None:
                continue
            if isinstance(p, list):
                chunks.extend(str(x) for x in p)
            elif isinstance(p, dict):
                chunks.append(json.dumps(p))
            else:
                chunks.append(str(p))
        return " ".join(chunks)
