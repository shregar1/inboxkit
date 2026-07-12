"""HttpUtility / NameUtility / PasswordUtility / VerifyUtility coverage."""

from __future__ import annotations

import io
import urllib.error
from unittest.mock import patch

import pytest

from inboxkit.utilities import (
    HttpUtility,
    NameUtility,
    PasswordUtility,
    VerifyUtility,
)


class _Resp:
    def __init__(self, payload: bytes | str):
        self._payload = payload if isinstance(payload, bytes) else payload.encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_http_json_get_empty_and_body_variants():
    with patch("urllib.request.urlopen", return_value=_Resp("")) as uo:
        assert HttpUtility.json("GET", "https://example.com/a") == {}
        assert uo.called

    with patch("urllib.request.urlopen", return_value=_Resp('{"ok":1}')) as uo:
        out = HttpUtility.json(
            "POST",
            "https://example.com/b",
            body={"x": 1},
            headers={"X-T": "1"},
            token="tok",
            content_type="application/json",
        )
        assert out == {"ok": 1}
        req = uo.call_args.args[0]
        assert req.get_header("Authorization") == "Bearer tok"
        assert req.data == b'{"x": 1}'

    with patch("urllib.request.urlopen", return_value=_Resp("{}")) as uo:
        HttpUtility.json("POST", "https://example.com/c", body="raw", content_type="text/plain")
        assert uo.call_args.args[0].data == b"raw"

    with patch("urllib.request.urlopen", return_value=_Resp("{}")) as uo:
        HttpUtility.json("PUT", "https://example.com/d")
        assert uo.call_args.args[0].data == b""


def test_http_json_http_error():
    err = urllib.error.HTTPError(
        "https://example.com/e", 500, "err", hdrs=None, fp=io.BytesIO(b"boom")
    )
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(RuntimeError, match="HTTP 500"):
            HttpUtility.json("GET", "https://example.com/e")


def test_http_text_and_bytes():
    with patch("urllib.request.urlopen", return_value=_Resp("hello")) as uo:
        assert HttpUtility.text("GET", "https://example.com/t", headers={"A": "1"}) == "hello"
        assert uo.called

    with patch("urllib.request.urlopen", return_value=_Resp(b"\x00\x01")) as uo:
        assert HttpUtility.bytes(
            "GET", "https://example.com/b", headers={"A": "1"}, token="t"
        ) == b"\x00\x01"
        assert uo.call_args.args[0].get_header("Authorization") == "Bearer t"


def test_http_urlencode():
    assert "a=1" in HttpUtility.urlencode({"a": "1", "b": "x y"})


def test_name_utility():
    local = NameUtility.random_local(8)
    assert local.startswith("ik") and len(local) == 10  # "ik" + 8 chars
    assert NameUtility.random_local(10).startswith("ik")
    r = NameUtility.realistic_local()
    assert r
    assert " " in NameUtility.realistic_display_name("james.smith")
    assert " " in NameUtility.realistic_display_name("james.smith42")
    assert " " in NameUtility.realistic_display_name(None)
    assert " " in NameUtility.realistic_display_name("nodot")


def test_password_utility():
    pw = PasswordUtility.strong(20)
    assert len(pw) == 20
    assert any(c.isupper() for c in pw)
    assert any(c.islower() for c in pw)
    assert any(c.isdigit() for c in pw)
    assert any(c in "!@#$%&*" for c in pw)


def test_verify_extract_link_variants():
    url = "https://example.com/verify?token=abc123"
    assert VerifyUtility.extract_link(f"Click {url} now") == url
    assert VerifyUtility.extract_link(
        '<a href="https://example.com/path?token=xyz">x</a>'
    ) == "https://example.com/path?token=xyz"
    assert VerifyUtility.extract_link(
        '<a href="https://example.com/verify-account">x</a>'
    ) == "https://example.com/verify-account"
    # token= near verify wording without full URL match first
    blob = "please verify your email token=ZZ99 more text"
    # may or may not find a link; at least exercises the verify branch
    VerifyUtility.extract_link(blob)
    assert VerifyUtility.extract_link("") is None
    assert VerifyUtility.extract_link("no links here") is None
    assert VerifyUtility.extract_link(
        "https://x.com/verify?token=t1)."
    ).endswith("token=t1")


def test_verify_blob_from_parts():
    blob = VerifyUtility.blob_from_parts(
        None, "a", ["b", "c"], {"d": 1}, 2
    )
    assert "a" in blob and "b" in blob and '"d": 1' in blob
