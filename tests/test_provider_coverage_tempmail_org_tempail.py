"""HTTP-mocked coverage for temp-mail.org and tempail leftovers."""

from __future__ import annotations

import io
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.temp_mail_org import TempMailOrgError
from inboxkit.errors.provider.tempail import TempailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.temp_mail_org.generate import TempMailOrgGenerateService
from inboxkit.services.providers.temp_mail_org.inbox import TempMailOrgInboxService
from inboxkit.services.providers.tempail._http import (
    TempailHttp,
    cookie_header_from_jar,
    extract_email,
    extract_session,
    extract_tarih,
    is_challenge,
    jar_from_cookie_header,
    parse_message_list,
    strip_tags,
)
from inboxkit.services.providers.tempail.generate import TempailGenerateService
from inboxkit.services.providers.tempail.inbox import TempailInboxService


# --- temp-mail.org ----------------------------------------------------------


def test_temp_mail_org_web_and_official_paths():
    web = TempMailOrgGenerateService(api_key="")
    official = TempMailOrgGenerateService(api_key="key")
    assert web.provider_name == "temp-mail.org"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {
            "domains": [
                {"name": "a.org", "type": "public"},
                {"name": "b.org", "type": "private"},
            ]
        }
        assert web.list_domains(backend="web") == ["a.org"]
        # no public → fallback names
        hj.return_value = {"domains": [{"name": "only.org", "type": "private"}]}
        assert web.list_domains(backend="web") == ["only.org"]

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = [{"name": "x.io"}, "y.io"]
        assert official.list_domains(backend="official") == ["x.io", "y.io"]
        hj.return_value = {"domains": [{"name": "n"}, {"domain": "d"}, "z"]}
        assert "n" in official.list_domains(backend="official")
        hj.return_value = {"data": ["plain"]}
        assert official.list_domains(backend="official") == ["plain"]

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"domains": [{"name": "tmp.org", "type": "public"}]},
            {"email": "u@tmp.org", "token": "tok"},
        ]
        inbox = web.mint(backend="web")
        assert inbox.meta["backend"] == "web"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"email": "o@io.com", "ttl": 1}
        oinbox = official.mint(backend="official", domain="io.com")
        assert oinbox.meta["backend"] == "official"

    ib_web = TempMailOrgInboxService(api_key="")
    ib_off = TempMailOrgInboxService(api_key="key")
    assert ib_off.provider_name == "temp-mail.org"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = [{"id": "1", "subject": "S", "body_text": "t"}]
        msgs = ib_web.list_messages(inbox)
        assert msgs[0]["id"] == "1"
        assert "S" in ib_web.read_message(inbox, msgs[0])
        hj.return_value = {"messages": [{"id": "2"}]}
        assert ib_web.list_messages(inbox)[0]["id"] == "2"
        hj.return_value = {"mail": [{"id": "3"}]}
        assert ib_web.list_messages(inbox)[0]["id"] == "3"
        hj.return_value = {}
        assert ib_web.list_messages(inbox) == []
        hj.return_value = [{"id": "1"}]
        assert ib_web.get_message(inbox, "1")["id"] == "1"
        hj.return_value = []
        with pytest.raises(TempMailOrgError):
            ib_web.get_message(inbox, "missing")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"messages": [{"id": "9", "subject": "O"}]}
        assert ib_off.list_messages(oinbox)[0]["id"] == "9"
        hj.return_value = [{"id": "8"}]
        assert ib_off.list_messages(oinbox)[0]["id"] == "8"
        hj.return_value = "bad"
        assert ib_off.list_messages(oinbox) == []
        hj.return_value = {"id": "9", "body_text": "full"}
        assert "full" in ib_off.read_message(oinbox, {"id": "9", "subject": "O"})
        hj.side_effect = RuntimeError("x")
        assert "O" in ib_off.read_message(oinbox, {"id": "9", "subject": "O"})
        hj.side_effect = None
        hj.return_value = {}
        ib_off.delete_message(oinbox, "9")
        ib_off.get_source(oinbox, "9")
        official.delete_email(oinbox)
        official.rate_limit()
        official.official_list_domains(api_key="key2")
        hj.return_value = {"email": "n@io.com"}
        official.official_create_email(api_key="key3", name="n")

    with patch("inboxkit.utilities.classes.HttpUtility.bytes", return_value=b"att"):
        assert ib_off.download_attachment(oinbox, "9", "a1") == b"att"

    with pytest.raises(UnauthorizedError):
        TempMailOrgGenerateService(api_key="").list_domains(backend="official")
    with pytest.raises(UnauthorizedError):
        TempMailOrgInboxService(api_key="").delete_message(oinbox, "1")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = RuntimeError("HTTP 500")
        with pytest.raises(TempMailOrgError):
            web.list_domains(backend="web")
        with pytest.raises(TempMailOrgError):
            official.list_domains(backend="official")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"domains": None}
        with pytest.raises(TempMailOrgError):
            web.list_domains(backend="web")
        hj.return_value = {"domains": "not-a-list"}
        with pytest.raises(TempMailOrgError):
            official.list_domains(backend="official")
        hj.return_value = {}
        with pytest.raises(TempMailOrgError):
            official.create_email(backend="official")
        hj.return_value = "bad"
        with pytest.raises(TempMailOrgError):
            web.create_email(name="n", domain="d.org", backend="web")
        hj.return_value = {"domains": []}
        with pytest.raises(TempMailOrgError):
            web.create_email(backend="web")

    with patch.object(
        web,
        "create_email",
        side_effect=[
            Exception("422 already"),
            {"email": "u@tmp.org", "token": "tok"},
        ],
    ):
        got = web.mint(backend="web", domain="tmp.org")
        assert got.token == "tok"

    with patch.object(
        web,
        "create_email",
        side_effect=[Exception("422 already")] * 6,
    ):
        with pytest.raises(TempMailOrgError, match="could not mint"):
            web.mint(backend="web", domain="tmp.org")

    with patch.object(web, "create_email", side_effect=Exception("fatal boom")):
        with pytest.raises(TempMailOrgError, match="fatal"):
            web.mint(backend="web", domain="tmp.org")

    with patch.object(
        web, "create_email", return_value={"email": "", "token": ""}
    ):
        with pytest.raises(TempMailOrgError, match="bad create"):
            web.mint(backend="web", domain="tmp.org")

    with patch.object(official, "create_email", return_value={"ttl": 1}):
        with pytest.raises(TempMailOrgError, match="bad mint"):
            official.mint(backend="official")

    with patch.object(
        ib_off, "get_message", side_effect=RuntimeError("x")
    ):
        assert "S" in ib_off.read_message(
            oinbox, {"id": "1", "subject": "S"}
        )
    assert "S" in ib_off.read_message(oinbox, {"subject": "S"})  # no mid

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "bad"
        with pytest.raises(TempMailOrgError):
            ib_off.get_message(oinbox, "1")


# --- tempail helpers / leftovers --------------------------------------------


def test_tempail_helpers_and_http_edges():
    assert strip_tags("<b>Hi &amp; you</b>") == "Hi & you"
    assert is_challenge("g-recaptcha here")
    assert is_challenge("bot-kontrol.php")
    assert is_challenge("please verify that you are not a robot")
    assert extract_tarih('tarih="99"') == "99"
    assert extract_tarih("nope") is None
    assert extract_email('<input id="email_input" value="a@b.com">') == "a@b.com"
    assert extract_email("nothing") is None
    # bad cfemail
    assert extract_email('data-cfemail="zz"') is None

    with pytest.raises(TempailError) as ei:
        extract_session('var oturum=""; var tarih="1";')
    assert "oturum" in ei.value.code or "no_oturum" in ei.value.code

    # fallback list parse without mail_ id
    html = """
    <ul><li><div class="gonderen">Bob</div><div class="konu">Sub</div></li></ul>
    """
    msgs = parse_message_list(html)
    assert any(m.get("from") == "Bob" for m in msgs)

    with pytest.raises(TempailError):
        parse_message_list("<title>Verifying your request, please wait...</title>")

    jar = jar_from_cookie_header("a=1; b=2; ; bad", domain="tempail.com")
    assert "a=1" in cookie_header_from_jar(jar)
    empty = jar_from_cookie_header("", domain="tempail.com")
    assert cookie_header_from_jar(empty) == ""


def test_tempail_http_request_paths():
    http = TempailHttp("sid=1", site="https://tempail.com")

    class _Resp:
        def read(self):
            return b'{"ok":1}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch.object(http._opener, "open", return_value=_Resp()):
        assert '"ok"' in http.request("POST", "https://tempail.com/x", form={"a": 1, "veri": ["1", "2"]})
        assert http.post_json("https://tempail.com/x", {"oturum": "t"}) == {"ok": 1}

    with patch.object(http._opener, "open", return_value=_Resp()):
        # empty / non-json post_json
        class _Empty:
            def read(self):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with patch.object(http._opener, "open", return_value=_Empty()):
            assert http.post_json("https://tempail.com/x", {}) == {}

        class _Plain:
            def read(self):
                return b"not-json"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with patch.object(http._opener, "open", return_value=_Plain()):
            assert http.post_json("https://tempail.com/x", {}) == {"raw": "not-json"}

        class _Captcha:
            def read(self):
                return b"Verifying your request, please wait..."

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with patch.object(http._opener, "open", return_value=_Captcha()):
            with pytest.raises(TempailError):
                http.post_json("https://tempail.com/x", {})

    err304 = urllib.error.HTTPError(
        "https://tempail.com/x", 304, "Not Modified", hdrs=None, fp=io.BytesIO(b"")
    )
    with patch.object(http._opener, "open", side_effect=err304):
        assert http.request("GET", "https://tempail.com/x") == ""

    err500 = urllib.error.HTTPError(
        "https://tempail.com/x", 500, "err", hdrs=None, fp=io.BytesIO(b"fail")
    )
    with patch.object(http._opener, "open", side_effect=err500):
        with pytest.raises(TempailError, match="HTTP 500"):
            http.request("GET", "https://tempail.com/x")

    with patch.object(http._opener, "open", side_effect=OSError("net")):
        with pytest.raises(TempailError, match="request failed"):
            http.request("GET", "https://tempail.com/x")


def test_tempail_inbox_delete_mark_recover_captcha(monkeypatch):
    gen = TempailGenerateService()
    ib = TempailInboxService()
    assert gen.provider_name == "tempail"

    inbox = TempInbox(
        address="a@necub.com",
        provider="tempail",
        token="tok",
        meta={
            "oturum": "tok",
            "tarih": "1",
            "cookie": "",
            "apis": dict(gen.DEFAULT_APIS),
        },
    )

    def fake_request(self, method, url, *, form=None, timeout=30):
        if "sil" in url or "duzelt" in url:
            return "ok"
        if "sifre" in url:
            return '{"qr":"1"}'
        if "kontrol" in url:
            if form and form.get("force_captcha"):
                return "Verifying your request"
            return '<ul class="mailler"><li id="mail_1" onclick="mail_oku(\'1\',\'aa\')"><div class="gonderen">A</div><div class="konu">S</div></li></ul><script>tarih="2";</script>'
        if "oku" in url:
            return "<div>body</div>"
        return "{}"

    monkeypatch.setattr(TempailHttp, "request", fake_request)
    ib.delete_message(inbox, "1", alt_id="aa")
    ib.mark_message(inbox, "1", alt_id="aa")
    assert gen.recover_qr(inbox).get("qr") == "1" or gen.recover_qr(inbox) == {"qr": "1"}

    # recover without sifre in resolved apis
    with patch.object(gen, "_apis", return_value={"kontrol": "https://x/kontrol"}):
        with pytest.raises(TempailError):
            gen.recover_qr(inbox)

    # captcha on poll / read
    def captcha_request(self, method, url, *, form=None, timeout=30):
        return "Verifying your request, please wait..."

    monkeypatch.setattr(TempailHttp, "request", captcha_request)
    with pytest.raises(TempailError):
        ib.poll_inbox(inbox)
    with pytest.raises(TempailError):
        ib.get_message(inbox, "1")

    # read_message fallback when get_message fails
    monkeypatch.setattr(
        TempailHttp,
        "request",
        lambda self, method, url, *, form=None, timeout=30: (_ for _ in ()).throw(RuntimeError("x"))
        if "oku" in url
        else '<li id="mail_1"><div class="gonderen">A</div><div class="konu">S</div></li>',
    )
    # simpler: patch get_message
    with patch.object(ib, "get_message", side_effect=RuntimeError("x")):
        assert "S" in ib.read_message(inbox, {"id": "1", "subject": "S", "from": "A"})
    assert "only" in ib.read_message(inbox, {"subject": "only"})

    # fetch_session missing email
    with patch.object(
        gen,
        "_client",
        return_value=MagicMock(
            get=lambda url: 'var oturum="abc"; var tarih="1";',
            cookie="",
        ),
    ):
        with patch(
            "inboxkit.services.providers.tempail.generate.extract_session",
            return_value={"oturum": "abc", "tarih": "1", "email": None, "apis": {}},
        ):
            with pytest.raises(TempailError):
                gen.fetch_session()

    # _apis from dict session
    assert "kontrol" in gen._apis({"apis": {"kontrol": "https://custom/kontrol"}})

    # meta None persist
    inbox2 = TempInbox(address="a@b.c", provider="tempail", token="t", meta=None)  # type: ignore[arg-type]
    inbox2.meta = None  # force
    http = TempailHttp("")
    ib._persist_cookie(inbox2, http)
    assert inbox2.meta["cookie"] == http.cookie
