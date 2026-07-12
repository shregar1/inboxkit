"""HTTP-mocked coverage for guerrillamail, maildrop, mailtm, secmail."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from inboxkit.errors.provider.guerrillamail import GuerrillaMailError
from inboxkit.errors.provider.maildrop import MailDropError
from inboxkit.errors.provider.mailtm import MailTmError
from inboxkit.errors.provider.secmail import SecMailError
from inboxkit.models import TempInbox
from inboxkit.services.providers.guerrillamail.generate import GuerrillaMailGenerateService
from inboxkit.services.providers.guerrillamail.inbox import GuerrillaMailInboxService
from inboxkit.services.providers.maildrop.generate import MailDropGenerateService
from inboxkit.services.providers.maildrop.inbox import MailDropInboxService
from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
from inboxkit.services.providers.secmail.generate import SecMailGenerateService
from inboxkit.services.providers.secmail.inbox import SecMailInboxService


# --- GuerrillaMail ----------------------------------------------------------


def test_guerrillamail_mint_list_read_delete_extend_forget():
    gen = GuerrillaMailGenerateService()
    ib = GuerrillaMailInboxService()
    assert gen.provider_name == "guerrillamail"
    assert ib.provider_name == "guerrillamail"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"sid_token": "sid1", "email_addr": "old@guerrillamailblock.com", "email_timestamp": 1},
            {"sid_token": "sid2", "email_addr": "user@guerrillamailblock.com", "email_timestamp": 2},
        ]
        inbox = gen.mint()
        assert inbox.address == "user@guerrillamailblock.com"
        assert inbox.token == "sid2"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"list": [{"mail_id": "9", "mail_subject": "Hi", "mail_excerpt": "ex"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["mail_id"] == "9"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"mail_body": "full body", "mail_subject": "Hi"}
        body = ib.read_message(inbox, msgs[0])
        assert "full body" in body

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = RuntimeError("down")
        assert "Hi" in ib.read_message(inbox, {"mail_id": "9", "mail_subject": "Hi"})

    assert ib.read_message(inbox, {"mail_subject": "only"}) == "only"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = ["ok"]
        assert ib.delete_messages(inbox, ["9", "10"]) == ["ok"]

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"extended": True}
        assert gen.extend(inbox)["extended"] is True
        hj.return_value = {}
        gen.forget_me(inbox)

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "bad"
        with pytest.raises(GuerrillaMailError):
            gen.get_email_address()
        with pytest.raises(GuerrillaMailError):
            gen.set_email_user("s", "u")
        with pytest.raises(GuerrillaMailError):
            gen.extend(inbox)
        with pytest.raises(GuerrillaMailError):
            ib.fetch_email(inbox, "1")

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"list": "nope"}
        assert ib.list_messages(inbox) == []
        hj.return_value = "x"
        assert ib.check_email(inbox) == {}
        assert ib.get_email_list(inbox) == {}


def test_guerrillamail_mint_missing_email():
    gen = GuerrillaMailGenerateService()
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"sid_token": "sid1", "email_addr": ""},
            {"sid_token": "sid2"},
        ]
        with pytest.raises(GuerrillaMailError):
            gen.mint()


# --- MailDrop ---------------------------------------------------------------


def test_maildrop_generate_and_inbox():
    gen = MailDropGenerateService()
    ib = MailDropInboxService()
    assert gen.provider_name == "maildrop"

    inbox = gen.mint()
    assert inbox.address.endswith("@maildrop.cc")
    assert inbox.meta["mailbox"]

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"data": {"ping": "pong"}}
        assert gen.ping("hi") == "pong"
        hj.return_value = {"data": {"statistics": {"blocked": 1, "saved": 2}}}
        assert gen.statistics()["blocked"] == 1
        hj.return_value = {"data": {"status": "ok"}}
        assert gen.status() == "ok"
        hj.return_value = {"data": {"altinbox": "altbox"}}
        assert gen.altinbox("x") == "altbox"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {
            "data": {"inbox": [{"id": "m1", "subject": "S", "mailfrom": "a@b.c"}]}
        }
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "m1"
        hj.return_value = {
            "data": {"message": {"id": "m1", "subject": "S", "html": "<b>hi</b>", "data": "txt"}}
        }
        assert "hi" in ib.read_message(inbox, msgs[0])
        hj.return_value = {"data": {"delete": True}}
        assert ib.delete_message(inbox, "m1") is True

    assert ib.read_message(inbox, {"subject": "only"}) == "only"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"errors": [{"message": "fail"}]}
        with pytest.raises(MailDropError):
            gen.ping()
        hj.return_value = {"errors": ["plain"]}
        with pytest.raises(MailDropError):
            ib.list_messages(inbox)
        hj.return_value = {"data": {"inbox": "bad"}}
        assert ib.list_messages(inbox) == []
        hj.return_value = {"data": {"message": "bad"}}
        with pytest.raises(MailDropError):
            ib.get_message(inbox, "x")
        hj.return_value = "notdict"
        assert gen._graphql("{x}") == {}


# --- Mail.tm ----------------------------------------------------------------


def test_mailtm_mint_and_inbox_ops():
    gen = MailTmGenerateService()
    ib = MailTmInboxService()
    assert gen.provider_name == "mail.tm"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"hydra:member": [{"domain": "mail.tm", "isActive": True}]},
            {"id": "acc1"},
            {"token": "tok1"},
        ]
        inbox = gen.mint()
        assert inbox.token == "tok1"
        assert inbox.meta["account_id"] == "acc1"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"hydra:member": [{"id": "m1", "subject": "Hi", "intro": "in"}]}
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == "m1"
        hj.return_value = {"id": "m1", "subject": "Hi", "text": "body", "html": "<p>x</p>"}
        assert "body" in ib.read_message(inbox, msgs[0])
        hj.return_value = {}
        ib.delete_message(inbox, "m1")
        hj.return_value = {"seen": True}
        assert ib.mark_seen(inbox, "m1")["seen"] is True
        hj.return_value = {"downloadUrl": "u"}
        assert ib.get_source(inbox, "m1")["downloadUrl"] == "u"

    assert "sub" in ib.read_message(inbox, {"subject": "sub", "intro": "i"})

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"id": "d1", "domain": "mail.tm"}
        assert gen.get_domain("d1")["id"] == "d1"
        hj.return_value = {"id": "acc1"}
        assert gen.get_account(inbox, "acc1")["id"] == "acc1"
        hj.return_value = {"id": "acc1"}
        assert gen.me(inbox)["id"] == "acc1"
        hj.return_value = {}
        gen.delete_account(inbox)
        # delete via /me when no account_id
        inbox2 = TempInbox(address="a@mail.tm", provider="mail.tm", token="t", meta={})
        hj.side_effect = [{"id": "fromme"}, {}]
        gen.delete_account(inbox2)


def test_mailtm_errors_and_retry():
    gen = MailTmGenerateService()
    ib = MailTmInboxService()

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = []
        with pytest.raises(MailTmError, match="no domains"):
            gen.mint()

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"hydra:member": [{"name": "mail.tm", "isActive": False}]},
            RuntimeError("HTTP 422 already used"),
            {"id": "a"},
            {"token": "t"},
        ]
        # first create fails with already used, second succeeds
        inbox = gen.mint()
        assert inbox.token == "t"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"hydra:member": [{"domain": "mail.tm"}]},
            RuntimeError("HTTP 500 boom"),
        ]
        with pytest.raises(MailTmError):
            gen.mint()

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "bad"
        with pytest.raises(MailTmError):
            gen.get_domain("x")
        with pytest.raises(MailTmError):
            gen.create_account("a@b.c", "pw")
        with pytest.raises(MailTmError):
            gen.get_token("a@b.c", "pw")
        with pytest.raises(MailTmError):
            gen.get_account(
                TempInbox(address="a@b.c", provider="mail.tm", token="t"), "1"
            )
        with pytest.raises(MailTmError):
            gen.me(TempInbox(address="a@b.c", provider="mail.tm", token="t"))
        with pytest.raises(MailTmError):
            ib.get_message(
                TempInbox(address="a@b.c", provider="mail.tm", token="t"), "1"
            )
        with pytest.raises(MailTmError):
            ib.get_source(
                TempInbox(address="a@b.c", provider="mail.tm", token="t"), "1"
            )

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = {"token": None}
        with pytest.raises(MailTmError):
            gen.get_token("a@b.c", "pw")

    assert MailTmGenerateService._members([{"a": 1}, "x"]) == [{"a": 1}]
    assert MailTmGenerateService._members({"member": [{"a": 1}]}) == [{"a": 1}]
    assert MailTmGenerateService._members("x") == []
    assert MailTmInboxService._as_list([{"a": 1}]) == [{"a": 1}]
    assert MailTmInboxService._as_list({"hydra:member": [{"a": 1}]}) == [{"a": 1}]
    assert MailTmInboxService._as_list(None) == []

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [{"id": None}, {}]
        inbox = TempInbox(address="a@mail.tm", provider="mail.tm", token="t", meta={})
        with pytest.raises(MailTmError, match="account id"):
            gen.delete_account(inbox)


def test_mailtm_mint_retry_exhausted():
    gen = MailTmGenerateService()
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = [
            {"hydra:member": [{"domain": "mail.tm"}]},
            *([RuntimeError("HTTP 422 already used")] * 12),
        ]
        with pytest.raises(MailTmError, match="could not mint"):
            gen.mint()


# --- 1secmail ---------------------------------------------------------------


def test_secmail_mint_list_read_download():
    gen = SecMailGenerateService()
    ib = SecMailInboxService()
    assert gen.provider_name == "1secmail"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = ["a@1secmail.com", "b@1secmail.com"]
        assert gen.list_domains()[0] == "a@1secmail.com"
        hj.return_value = ["user@1secmail.com"]
        inbox = gen.mint()
        assert inbox.meta["login"] == "user"

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = [{"id": 1, "subject": "S", "from": "x@y.z"}]
        msgs = ib.list_messages(inbox)
        assert msgs[0]["id"] == 1
        hj.return_value = {
            "id": 1,
            "subject": "S",
            "textBody": "hello",
            "htmlBody": "<b>h</b>",
        }
        assert "hello" in ib.read_message(inbox, msgs[0])

    assert "S" in ib.read_message(inbox, {"subject": "S", "from": "f"})

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.side_effect = RuntimeError("fail")
        assert "S" in ib.read_message(inbox, {"id": 1, "subject": "S", "from": "f"})

    with patch("inboxkit.utilities.classes.HttpUtility.bytes", return_value=b"PDF") as hb:
        assert ib.download_attachment(inbox, 1, "a.pdf") == b"PDF"
        assert "download" in hb.call_args.args[1]

    # _parts fallback from address
    bare = TempInbox(address="x@1secmail.org", provider="1secmail", token="t", meta={})
    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "notlist"
        assert ib.list_messages(bare) == []

    with patch("inboxkit.utilities.classes.HttpUtility.json") as hj:
        hj.return_value = "bad"
        with pytest.raises(SecMailError):
            gen.list_domains()
        with pytest.raises(SecMailError):
            gen.gen_random_mailbox()
        hj.return_value = ["notanemail"]
        with pytest.raises(SecMailError):
            gen.mint()
        hj.return_value = "bad"
        with pytest.raises(SecMailError):
            ib.get_message(inbox, 1)
