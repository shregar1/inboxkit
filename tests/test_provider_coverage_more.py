"""HTTP-mocked coverage for smailpro, temp-mail.app, tempmail.lol, tempy."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from inboxkit.errors import UnauthorizedError
from inboxkit.errors.provider.smailpro import SmailProError
from inboxkit.errors.provider.temp_mail_app import TempMailAppError
from inboxkit.errors.provider.tempmail_lol import TempMailLolError
from inboxkit.errors.provider.tempy import TempyError
from inboxkit.models import TempInbox
from inboxkit.services.providers.smailpro.generate import SmailProGenerateService
from inboxkit.services.providers.smailpro.inbox import SmailProInboxService
from inboxkit.services.providers.temp_mail_app.generate import TempMailAppGenerateService
from inboxkit.services.providers.temp_mail_app.inbox import TempMailAppInboxService
from inboxkit.services.providers.tempmail_lol.generate import TempMailLolGenerateService
from inboxkit.services.providers.tempmail_lol.inbox import TempMailLolInboxService
from inboxkit.services.providers.tempy.generate import TempyGenerateService
from inboxkit.services.providers.tempy.inbox import TempyInboxService


# --- SmailPro ---------------------------------------------------------------


def test_smailpro_outlook_list_inbox_read_remove_attachments():
    gen = SmailProGenerateService(api_key="k")
    ib = SmailProInboxService(api_key="k")
    assert gen.provider_name == "smailpro"
    assert ib.provider_name == "smailpro"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"email": "o@outlook.com", "timestamp": 9, "type": "alias"}
        inbox = gen.mint(kind="outlook")
        assert inbox.meta["kind"] == "outlook"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"items": []}
        assert "items" in gen.list_gmail()
        assert "items" in gen.list_outlook()

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"messages": [{"mid": "m1", "subject": "S", "from": "a"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "m1"
        hj.return_value = {"body": "hello"}
        assert "hello" in ib.read_message(inbox, msgs[0])

    email_inbox = TempInbox(
        address="e@ex.com", provider="smailpro", token="e", meta={"kind": "email"}
    )
    gmail_inbox = TempInbox(
        address="g@gmail.com",
        provider="smailpro",
        token="g",
        meta={"kind": "gmail", "timestamp": 1},
    )
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"messages": [{"id": "1"}]}
        assert ib.list_messages(email_inbox)
        assert ib.list_messages(gmail_inbox)
        hj.return_value = {"body": "x"}
        assert ib.get_message(email_inbox, "1")
        assert ib.get_message(gmail_inbox, "1")
        assert ib.get_message(inbox, "1")
        hj.return_value = {"ok": 1}
        ib.remove_gmail_message(gmail_inbox, "1")
        ib.list_attachments(email_inbox, "1")

    assert ib.read_message(email_inbox, {"subject": "only"}) == "only"

    with pytest.raises(SmailProError):
        ib.remove_gmail_message(email_inbox, "1")
    with pytest.raises(SmailProError):
        ib.list_attachments(gmail_inbox, "1")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = RuntimeError("HTTP 401")
        with pytest.raises(SmailProError):
            gen.list_domains()
        with pytest.raises(SmailProError):
            ib.list_messages(email_inbox)

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"domains": None}
        with pytest.raises(SmailProError):
            gen.list_domains()
        hj.return_value = {}
        with pytest.raises(SmailProError):
            gen.random_gmail()
        with pytest.raises(SmailProError):
            gen.random_outlook()
        hj.return_value = "bad"
        with pytest.raises(SmailProError):
            gen.list_gmail()
        with pytest.raises(SmailProError):
            gen.list_outlook()
        with pytest.raises(SmailProError):
            ib.get_message(email_inbox, "1")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"domains": []}
        with pytest.raises(SmailProError, match="no domains"):
            gen.mint(kind="email")

    bare = SmailProInboxService(api_key="")
    with pytest.raises(UnauthorizedError):
        bare.list_messages(email_inbox)


# --- temp-mail.app ----------------------------------------------------------


def test_temp_mail_app_mint_and_list():
    gen = TempMailAppGenerateService()
    ib = TempMailAppInboxService()
    assert gen.provider_name == "temp-mail.app"

    with patch("inboxkit.utilities.classes.HttpUtility.text") as ht:
        ht.return_value = '{"email":"a@temp-mail.app"}'
        inbox = gen.mint()
        assert inbox.address == "a@temp-mail.app"
        assert inbox.meta["visitor_id"]

    with patch("inboxkit.utilities.classes.HttpUtility.text") as ht:
        ht.return_value = '{"data":{"email":"b@temp-mail.app"}}'
        assert gen.create_address()["email"] == "b@temp-mail.app"
        ht.return_value = '{"email":{"email":"c@temp-mail.app"}}'
        assert gen.create_address()["email"] == "c@temp-mail.app"
        ht.return_value = "not-json"
        with pytest.raises(TempMailAppError):
            gen.create_address()
        ht.return_value = '{"email":"bad"}'
        with pytest.raises(TempMailAppError):
            gen.create_address()

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = [{"subject": "S", "from": "f", "body": "b"}]
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "0"
        assert "S" in ib.read_message(inbox, msgs[0])
        hj.return_value = {"data": [{"id": "x", "subject": "Y"}]}
        assert ib.list_messages(inbox)[0]["id"] == "x"
        hj.side_effect = RuntimeError("down")
        assert ib.list_messages(inbox) == []
        hj.side_effect = None
        hj.return_value = {"data": "bad"}
        assert ib.list_messages(inbox) == []


# --- tempmail.lol -----------------------------------------------------------


def test_tempmail_lol_create_mint_inbox_webhooks():
    gen = TempMailLolGenerateService()
    ib = TempMailLolInboxService()
    assert gen.provider_name == "tempmail.lol"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"address": "a@tempmail.lol", "token": "tok"}
        inbox = gen.mint()
        assert inbox.token == "tok"

        hj.return_value = {"address": "b@tempmail.lol", "token": "t2"}
        data = gen.create_inbox(prefix="pre", domain="x.com", community=True, api_key="key")
        assert data["token"] == "t2"
        assert hj.call_args.args[0] == "POST"

        hj.return_value = {"ok": True}
        gen.set_webhook("https://hook", api_key="k")
        gen.remove_webhook(api_key="k")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"email": [{"subject": "Hi", "body": "b", "from": "f"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "0"
        assert "Hi" in ib.read_message(inbox, msgs[0])
        hj.return_value = None
        assert ib.check_inbox("t") == []
        hj.return_value = {"email": "bad"}
        assert ib.check_inbox("t") == []

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "bad"
        with pytest.raises(TempMailLolError):
            gen.create_inbox()
        hj.return_value = {"address": "", "token": ""}
        with pytest.raises(TempMailLolError):
            gen.create_inbox()


# --- tempy ------------------------------------------------------------------


def test_tempy_mint_list_get_delete():
    gen = TempyGenerateService()
    ib = TempyInboxService()
    assert gen.provider_name == "tempy.email"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {
            "email": "a@tempy.email",
            "expiresAt": "x",
            "webUrl": "https://tempy.email/a",
            "secondsRemaining": 60,
        }
        inbox = gen.mint()
        assert inbox.address == "a@tempy.email"
        assert inbox.view_url == "https://tempy.email/a"

        hj.return_value = {"email": "b@tempy.email"}
        gen.create_mailbox(domain="tempy.email", webhook_url="https://h", api_key="k")
        hj.return_value = {"email": "b@tempy.email", "active": True}
        assert gen.get_mailbox("b@tempy.email")["active"] is True
        hj.return_value = {}
        gen.delete_mailbox("b@tempy.email")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"messages": [{"subject": "S", "body": "b"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "0"
        assert "S" in ib.read_message(inbox, msgs[0])
        hj.return_value = [{"id": "1", "subject": "T"}]
        assert ib.list_messages(inbox)[0]["id"] == "1"
        hj.return_value = {"messages": None}
        assert ib.list_messages(inbox) == []

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {}
        with pytest.raises(TempyError):
            gen.create_mailbox()
        hj.return_value = "bad"
        with pytest.raises(TempyError):
            gen.get_mailbox("x")
        hj.return_value = {"foo": 1}
        with pytest.raises(TempyError):
            gen.mint()
