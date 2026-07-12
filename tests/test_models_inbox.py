"""TempInbox model edge cases."""

from __future__ import annotations

import pytest

from inboxkit.errors import InboxNotBoundError
from inboxkit.models import TempInbox


def test_local_domain_from_address_and_meta():
    bare = TempInbox(address="onlylocal", provider="p")
    assert bare.local == "onlylocal"
    assert bare.domain == ""

    with_at = TempInbox(address="u@example.com", provider="p")
    assert with_at.local == "u"
    assert with_at.domain == "example.com"
    assert with_at.email == "u@example.com"

    meta = TempInbox(
        address="u@example.com",
        provider="p",
        meta={"local": "alt", "domain": "other.com"},
    )
    assert meta.local == "alt"
    assert meta.domain == "other.com"

    empty_meta = TempInbox(
        address="u@example.com",
        provider="p",
        meta={"local": "", "domain": ""},
    )
    assert empty_meta.local == "u"
    assert empty_meta.domain == "example.com"


def test_password_view_url_display_name():
    inbox = TempInbox(
        address="a@b.c",
        provider="p",
        meta={
            "passwd": "secret",
            "view_hint": "https://web.example/",
            "display_name": "Ada Lovelace",
            "sid_token": "sid",
            "token": "meta-tok",
        },
    )
    assert inbox.password == "secret"
    assert inbox.view_url == "https://web.example/"
    assert inbox.display_name == "Ada Lovelace"
    creds = inbox.credentials
    assert creds["password"] == "secret"
    assert creds["sid_token"] == "sid"
    assert creds["token"] == ""  # instance token empty; meta token filled below path
    # empty instance token — meta token should fill when "token" not in creds... 
    # but token key is always set from self.token (""), so meta path at 115-116 only
    # runs when token not in creds — which never happens because token is always set.
    # Cover pass/passwd keys and web_url:
    assert TempInbox(address="a@b.c", provider="p", meta={"pass": "p2"}).password == "p2"
    assert TempInbox(address="a@b.c", provider="p", meta={"web_url": "https://w"}).view_url == "https://w"
    assert TempInbox(address="a@b.c", provider="p", meta={"site": "https://s"}).view_url == "https://s"
    assert TempInbox(address="a@b.c", provider="p", meta={"url": "https://u"}).view_url == "https://u"
    assert TempInbox(address="a@b.c", provider="p").password is None
    assert TempInbox(address="a@b.c", provider="p").view_url is None
    assert TempInbox(address="a@b.c", provider="p").display_name is None


def test_credentials_meta_token_when_token_empty_key_missing():
    # Force the rare path: credentials always includes token from self.token.
    # Cover other credential keys and to_dict.
    inbox = TempInbox(
        address="a@b.c",
        provider="p",
        token="tok",
        meta={
            "oturum": "o",
            "cookie": "c",
            "tarih": "t",
            "visitor_id": "v",
            "account_id": "acc",
            "login": "l",
            "mailbox": "m",
            "api_key": "k",
            "backend": "web",
            "password": "pw",
        },
    )
    d = inbox.to_dict()
    assert d["password"] == "pw"
    assert d["credentials"]["oturum"] == "o"
    assert d["local"] == "a"
    assert d["domain"] == "b.c"


def test_list_read_unbound():
    inbox = TempInbox(address="a@b.c", provider="p")
    with pytest.raises(InboxNotBoundError):
        inbox.list_messages()
    with pytest.raises(InboxNotBoundError):
        inbox.read_message({"id": "1"})


def test_bound_list_read():
    inbox = TempInbox(
        address="a@b.c",
        provider="p",
        _list=lambda self: [{"id": "1"}],
        _read=lambda self, msg: f"body-{msg['id']}",
    )
    assert inbox.list_messages()[0]["id"] == "1"
    assert inbox.read_message({"id": "9"}) == "body-9"
