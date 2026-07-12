"""SDK surface tests — methods match researched public APIs (mocked HTTP)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from inboxkit.models import TempInbox
from inboxkit.services.providers.api_surfaces import API_SURFACES
from inboxkit.services.providers.maildrop.inbox import MailDropInboxService
from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
from inboxkit.services.providers.tempy.generate import TempyGenerateService


@pytest.mark.parametrize("provider,spec", sorted(API_SURFACES.items()))
def test_api_surface_declares_generate_and_inbox(provider, spec):
    assert isinstance(spec["generate"], list) and spec["generate"]
    assert isinstance(spec["inbox"], list) and spec["inbox"]


def test_mailtm_sdk_methods_exist():
    gen = MailTmGenerateService()
    inbox = MailTmInboxService()
    for name in API_SURFACES["mail.tm"]["generate"]:
        assert callable(getattr(gen, name))
    for name in API_SURFACES["mail.tm"]["inbox"]:
        assert callable(getattr(inbox, name))


def test_mailtm_delete_and_mark_seen_call_http():
    inbox = TempInbox(address="a@mail.tm", provider="mail.tm", token="tok", meta={"account_id": "acc1"})
    gen = MailTmGenerateService()
    msg = MailTmInboxService()
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {}
        gen.delete_account(inbox)
        assert hj.call_args.args[0] == "DELETE"
        assert "/accounts/acc1" in hj.call_args.args[1]
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"seen": True}
        out = msg.mark_seen(inbox, "m1")
        assert out["seen"] is True
        assert hj.call_args.args[0] == "PATCH"
        assert hj.call_args.kwargs.get("content_type") == "application/merge-patch+json"
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {}
        msg.delete_message(inbox, "m1")
        assert hj.call_args.args[0] == "DELETE"


def test_maildrop_delete_mutation():
    svc = MailDropInboxService()
    inbox = TempInbox(address="x@maildrop.cc", provider="maildrop", token="x", meta={"mailbox": "x"})
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"data": {"delete": True}}
        assert svc.delete_message(inbox, "abc") is True
        q = hj.call_args.kwargs["body"]["query"]
        assert "mutation" in q and "delete" in q


def test_tempy_delete_mailbox():
    svc = TempyGenerateService()
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {}
        svc.delete_mailbox("a@tempy.email")
        assert hj.call_args.args[0] == "DELETE"
        assert "/mailbox/" in hj.call_args.args[1]


def test_smailpro_mint_email_and_gmail():
    from inboxkit.errors import UnauthorizedError
    from inboxkit.services.providers.smailpro.generate import SmailProGenerateService

    bare = SmailProGenerateService(api_key="")
    with pytest.raises(UnauthorizedError):
        bare.list_domains()

    svc = SmailProGenerateService(api_key="test-key")
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"domains": ["example.com"]},
            {},  # create
        ]
        inbox = svc.mint(kind="email")
        assert inbox.provider == "smailpro"
        assert inbox.meta["kind"] == "email"
        assert "@example.com" in inbox.address
        assert hj.call_args_list[0].args[1].endswith("/v1/temp_email/domains")
        assert "/v1/temp_email/create" in hj.call_args_list[1].args[1]

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"email": "a@gmail.com", "timestamp": 123, "type": "alias"}
        inbox = svc.mint(kind="gmail")
        assert inbox.meta["kind"] == "gmail"
        assert inbox.address == "a@gmail.com"
        assert "/v1/temp_gmail/random" in hj.call_args.args[1]


def test_temp_mail_org_web_and_official_mint():
    from inboxkit.services.providers.temp_mail_org.generate import TempMailOrgGenerateService
    from inboxkit.services.providers.temp_mail_org.inbox import TempMailOrgInboxService

    web = TempMailOrgGenerateService(api_key="")
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"domains": [{"name": "tmp.org", "type": "public"}]},
            {"email": "a@tmp.org", "token": "tok"},
        ]
        inbox = web.mint(backend="web")
        assert inbox.meta["backend"] == "web"
        assert inbox.token == "tok"
        assert "/email/new" in hj.call_args_list[1].args[1]

    official = TempMailOrgGenerateService(api_key="key")
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"email": "u@example.com", "ttl": 86400}
        inbox = official.mint(backend="official")
        assert inbox.meta["backend"] == "official"
        assert inbox.address == "u@example.com"
        assert hj.call_args.args[0] == "POST"
        assert "/v1/emails" in hj.call_args.args[1]

    ib = TempMailOrgInboxService(api_key="key")
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"messages": [{"id": "1", "subject": "hi"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "1"
        assert "/emails/" in hj.call_args.args[1] and "/messages" in hj.call_args.args[1]


def test_temp_mail_io_is_alias_of_temp_mail_org():
    from inboxkit.enums import Provider
    from inboxkit.services.inbox import InboxService

    assert Provider.coerce("temp-mail.io") is Provider.TEMP_MAIL_ORG
    assert Provider.coerce("tempmail.io") is Provider.TEMP_MAIL_ORG
    svc = InboxService()
    names = {n for s in svc._specs for n in s.all_names()}
    assert "temp-mail.io" in names
    assert "temp-mail.org" in names
    assert "temp-mail.io" in svc._minters


_TEMPAIL_HOME = """
<html><head><script>
var url_api_kontrol="https://tempail.com/en/api/kontrol/";
var url_api_sil="https://tempail.com/en/api/sil/";
var url_api_yoket="https://tempail.com/en/api/yoket/";
var url_api_oku="https://tempail.com/en/api/oku/";
var url_api_duzelt="https://tempail.com/en/api/duzelt/";
var url_api_sifre="https://tempail.com/en/api/sifre/";
var oturum="abc123";var tarih="1700000000";
</script></head>
<body>
<span class="__cf_email__" data-cfemail="5a3b3633393f1a343f392f3874393537">[email&#160;protected]</span>
<input id="email_input" type="text" value="" readonly>
</body></html>
"""

_TEMPAIL_LIST = """
<script>tarih="1700000001";</script>
<ul class="mailler">
  <li class="baslik"><div class="gonderen">Sender</div></li>
  <li id="mail_9">
    <a href="#" onclick="mail_oku('9','xx')">
      <div class="gonderen">Alice &lt;a@x.com&gt;</div>
      <div class="konu">Hello</div>
      <div class="zaman">12:00</div>
    </a>
  </li>
</ul>
"""


def test_tempail_cfemail_and_list_parse():
    from inboxkit.services.providers.tempail._http import (
        decode_cfemail,
        parse_message_list,
    )

    # key 0x5a xor → alice@necub.com
    assert decode_cfemail("5a3b3633393f1a343f392f3874393537") == "alice@necub.com"
    msgs = parse_message_list(_TEMPAIL_LIST)
    assert len(msgs) == 1
    assert msgs[0]["id"] == "9"
    assert msgs[0]["alt_id"] == "xx"
    assert "Alice" in msgs[0]["from"]
    assert msgs[0]["subject"] == "Hello"


def test_tempail_mint_and_poll(monkeypatch):
    from inboxkit.services.providers.tempail._http import TempailHttp
    from inboxkit.services.providers.tempail.generate import TempailGenerateService
    from inboxkit.services.providers.tempail.inbox import TempailInboxService

    calls: list[tuple[str, str]] = []

    def fake_request(self, method, url, *, form=None, timeout=30):
        calls.append((method.upper(), url))
        if method.upper() == "GET":
            return _TEMPAIL_HOME
        if "kontrol" in url:
            return _TEMPAIL_LIST
        if "oku" in url:
            return "<div>Verify https://example.com/v?token=1</div>"
        if "yoket" in url:
            return '{"hata":"yok"}'
        return "{}"

    monkeypatch.setattr(TempailHttp, "request", fake_request)
    svc = TempailGenerateService()
    inbox = svc.mint()
    assert inbox.provider == "tempail"
    assert inbox.token == "abc123"
    assert inbox.address == "alice@necub.com"
    assert inbox.meta["oturum"] == "abc123"

    ib = TempailInboxService()
    msgs = ib.list_messages(inbox)
    assert msgs[0]["id"] == "9"
    assert inbox.meta["tarih"] == "1700000001"
    body = ib.read_message(inbox, msgs[0])
    assert "Verify" in body
    destroyed = svc.destroy_mailbox(inbox)
    assert destroyed.get("hata") == "yok"


def test_tempail_captcha_raises():
    from inboxkit.errors.provider.tempail import TempailError
    from inboxkit.services.providers.tempail._http import extract_session

    with pytest.raises(TempailError) as ei:
        extract_session("<title>Verifying your request, please wait...</title>")
    assert ei.value.code == "tempail_captcha"


def test_tempail_registered():
    from inboxkit.enums import Provider
    from inboxkit.services.inbox import InboxService

    assert Provider.coerce("tempail.com") is Provider.TEMPAIL
    assert "tempail" in InboxService()._minters


def test_tempmail_net_mint_and_poll(monkeypatch):
    from inboxkit.services.providers.tempail._http import TempailHttp
    from inboxkit.services.providers.tempmail_net.generate import TempmailNetGenerateService
    from inboxkit.services.providers.tempmail_net.inbox import TempmailNetInboxService

    home = """
    <html><head><script>
    var url_api_kontrol="https://tempmail.net/en/api/kontrol/";
    var url_api_sil="https://tempmail.net/en/api/sil/";
    var url_api_yoket="https://tempmail.net/en/api/yoket/";
    var url_api_oku="https://tempmail.net/en/api/oku/";
    var url_api_duzelt="https://tempmail.net/en/api/duzelt/";
    var oturum="netTok";var tarih="1700000100";
    </script></head>
    <body><input id="eposta_adres" value="user@tozya.com"></body></html>
    """
    listing = """
    <script>tarih="1700000101";</script>
    <ul class="mailler">
      <li id="mail_1" onclick="mail_oku('1','aa')">
        <div class="gonderen">Bob</div>
        <div class="konu">Hi</div>
      </li>
    </ul>
    """

    def fake_request(self, method, url, *, form=None, timeout=30):
        assert "tempmail.net" in self.site
        if method.upper() == "GET":
            return home
        if "kontrol" in url:
            return listing
        if "yoket" in url:
            return '{"hata":"yok"}'
        return ""

    monkeypatch.setattr(TempailHttp, "request", fake_request)
    svc = TempmailNetGenerateService()
    inbox = svc.mint()
    assert inbox.provider == "tempmail.net"
    assert inbox.address == "user@tozya.com"
    assert inbox.token == "netTok"
    msgs = TempmailNetInboxService().list_messages(inbox)
    assert msgs[0]["subject"] == "Hi"
    assert inbox.meta["tarih"] == "1700000101"


def test_tempmail_net_registered():
    from inboxkit.enums import Provider
    from inboxkit.services.inbox import InboxService

    assert Provider.coerce("tempmailnet") is Provider.TEMPMAIL_NET
    assert "tempmail.net" in InboxService()._minters
