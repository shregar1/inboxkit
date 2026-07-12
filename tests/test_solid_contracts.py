"""Unit tests — written to lock SOLID/DRY contracts (TDD)."""

from __future__ import annotations

import pytest

from inboxkit.errors import (
    AllProvidersFailedError,
    BadInputError,
    InboxNotBoundError,
    UnknownProviderError,
    VerifyTimeoutError,
)
from inboxkit.errors.provider import IProviderError, MailTmError
from inboxkit.models import TempInbox
from inboxkit.services.inbox import InboxService
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)
from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
from inboxkit.services.providers.registry import ProviderSpec
from inboxkit.services.providers.spec import ProviderSpec as SpecAlias
from inboxkit.utilities import VerifyUtility

assert SpecAlias is ProviderSpec


# --- models -----------------------------------------------------------------


def test_temp_inbox_unbound_raises_typed_error():
    inbox = TempInbox(address="a@b.c", provider="x")
    with pytest.raises(InboxNotBoundError):
        inbox.list_messages()
    with pytest.raises(InboxNotBoundError):
        inbox.read_message({})


def test_temp_inbox_delegates_to_bound_callables():
    calls: list[str] = []

    def _list(inbox: TempInbox) -> list[dict]:
        calls.append("list")
        return [{"id": "1"}]

    def _read(inbox: TempInbox, msg: dict) -> str:
        calls.append("read")
        return "body"

    inbox = TempInbox(address="a@b.c", provider="x", _list=_list, _read=_read)
    assert inbox.list_messages() == [{"id": "1"}]
    assert inbox.read_message({"id": "1"}) == "body"
    assert calls == ["list", "read"]


def test_temp_inbox_credentials_and_to_dict():
    inbox = TempInbox(
        address="jane.doe@mail.tm",
        provider="mail.tm",
        token="jwt-token",
        meta={
            "password": "secret",
            "account_id": "acc-1",
            "display_name": "Jane Doe",
            "local": "jane.doe",
            "domain": "mail.tm",
            "view_hint": "https://mail.tm/",
        },
    )
    assert inbox.email == "jane.doe@mail.tm"
    assert inbox.password == "secret"
    assert inbox.local == "jane.doe"
    assert inbox.domain == "mail.tm"
    creds = inbox.credentials
    assert creds["email"] == inbox.email
    assert creds["token"] == "jwt-token"
    assert creds["password"] == "secret"
    assert creds["account_id"] == "acc-1"
    dump = inbox.to_dict()
    assert dump["email"] == inbox.email
    assert dump["credentials"]["password"] == "secret"
    assert dump["meta"]["account_id"] == "acc-1"
    assert dump["view_url"] == "https://mail.tm/"
    assert dump["display_name"] == "Jane Doe"


# --- ISP --------------------------------------------------------------------


def test_generate_service_is_not_inbox_service():
    assert issubclass(MailTmGenerateService, IProviderGenerateService)
    assert not issubclass(MailTmGenerateService, IProviderInboxService)
    assert issubclass(MailTmInboxService, IProviderInboxService)
    assert not issubclass(MailTmInboxService, IProviderGenerateService)


def test_generate_has_mint_only_on_class():
    assert hasattr(MailTmGenerateService, "mint")
    # ISP: no stub list/read on generate class body beyond inheritance
    assert "list_messages" not in MailTmGenerateService.__dict__
    assert "read_message" not in MailTmGenerateService.__dict__
    assert "mint" not in MailTmInboxService.__dict__


# --- DIP / InboxService -----------------------------------------------------


class _FakeGenerate(IProviderGenerateService):
    def __init__(self, name: str, inbox: TempInbox | None = None, exc: Exception | None = None):
        self._name = name
        self._inbox = inbox
        self._exc = exc
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def mint(self) -> TempInbox:
        self.calls += 1
        if self._exc:
            raise self._exc
        assert self._inbox is not None
        return self._inbox


def test_create_inbox_unknown_provider_is_bad_input():
    svc = InboxService(specs=[], order=[])
    with pytest.raises(UnknownProviderError) as ei:
        svc.create_inbox("nope")
    assert isinstance(ei.value, BadInputError)


def test_create_inbox_uses_injected_spec_not_globals():
    target = TempInbox(address="t@x.com", provider="fake")
    fake = _FakeGenerate("fake", inbox=target)
    svc = InboxService(
        specs=[ProviderSpec("fake", ("f",), fake)],
        order=["fake"],
    )
    assert svc.create_inbox("f") is target
    assert fake.calls == 1


def test_create_inbox_auto_falls_through_and_aggregates():
    a = _FakeGenerate("a", exc=RuntimeError("a-down"))
    b_inbox = TempInbox(address="b@x.com", provider="b")
    b = _FakeGenerate("b", inbox=b_inbox)
    svc = InboxService(
        specs=[
            ProviderSpec("a", (), a),
            ProviderSpec("b", (), b),
        ],
        order=["a", "b"],
    )
    assert svc.create_inbox("auto") is b_inbox
    assert a.calls == 1 and b.calls == 1


def test_create_inbox_all_failed():
    a = _FakeGenerate("a", exc=RuntimeError("boom"))
    svc = InboxService(specs=[ProviderSpec("a", (), a)], order=["a"])
    with pytest.raises(AllProvidersFailedError):
        svc.create_inbox("auto")


def test_poll_verify_link_finds_link_without_real_sleep():
    link = "https://example.com/api/auth/verify-email?token=abc"

    def _list(_inbox: TempInbox) -> list[dict]:
        return [{"id": "1"}]

    def _read(_inbox: TempInbox, _msg: dict) -> str:
        return f"click {link}"

    inbox = TempInbox(
        address="a@b.c", provider="x", _list=_list, _read=_read
    )
    sleeps: list[float] = []
    svc = InboxService(
        specs=[],
        order=[],
        sleep=sleeps.append,
        clock=lambda: 0.0,
    )
    assert svc.poll_verify_link(inbox, timeout_secs=10, poll_every=1) == link
    assert sleeps == []  # found on first pass


def test_poll_verify_timeout():
    inbox = TempInbox(
        address="a@b.c",
        provider="x",
        _list=lambda _i: [],
        _read=lambda _i, _m: "",
    )
    t = {"now": 0.0}

    def clock() -> float:
        return t["now"]

    def sleep(dt: float) -> None:
        t["now"] += dt

    svc = InboxService(specs=[], order=[], sleep=sleep, clock=clock)
    with pytest.raises(VerifyTimeoutError):
        svc.poll_verify_link(inbox, timeout_secs=3, poll_every=1)


# --- errors / DRY verify ----------------------------------------------------


def test_provider_error_hierarchy():
    err = MailTmError("x")
    assert isinstance(err, IProviderError)
    assert err.provider == "mail.tm"


def test_extract_verify_link():
    html = 'Go <a href="https://example.com/api/auth/verify-email?token=TOK123">here</a>'
    assert VerifyUtility.extract_link(html).endswith("token=TOK123")
