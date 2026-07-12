"""TempMail public router tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DOCS = Path(__file__).resolve().parents[2]
if str(_DOCS) not in sys.path:
    sys.path.insert(0, str(_DOCS))

from inboxkit.enums import RouterMode
from inboxkit.errors import (
    BadInputError,
    UnprocessableError,
    UnknownProviderError,
    VerifyTimeoutError,
)
from inboxkit.factories import ProviderFactory, ProviderRegistration
from inboxkit.models import TempInbox
from inboxkit.router import ITempMailRouter, TempMail
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)


class _Gen(IProviderGenerateService):
    def __init__(self, name: str = "fake") -> None:
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def mint(self) -> TempInbox:
        return TempInbox(address=f"a@{self._name}.test", provider=self._name, token="t")

    def destroy_mailbox(self, inbox: TempInbox) -> str:
        return "gone"


class _FailGen(_Gen):
    def mint(self) -> TempInbox:
        raise RuntimeError(f"{self._name}-down")


class _Inbox(IProviderInboxService):
    def __init__(self, name: str = "fake") -> None:
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def list_messages(self, inbox: TempInbox) -> list[dict]:
        return [{"id": "1", "subject": "hi"}]

    def read_message(self, inbox: TempInbox, msg: dict) -> str:
        return f"body:{msg.get('id')}"

    def delete_message(self, inbox: TempInbox, message_id: str | int) -> None:
        return None


def _simple_factory() -> ProviderFactory:
    return ProviderFactory(
        [ProviderRegistration("fake", ("f",), _Gen, _Inbox)]
    )


def _two_factory(*, a_fails: bool = False) -> ProviderFactory:
    class GenA(_FailGen if a_fails else _Gen):
        def __init__(self) -> None:
            super().__init__("a")

    class GenB(_Gen):
        def __init__(self) -> None:
            super().__init__("b")

    class InA(_Inbox):
        def __init__(self) -> None:
            super().__init__("a")

    class InB(_Inbox):
        def __init__(self) -> None:
            super().__init__("b")

    return ProviderFactory(
        [
            ProviderRegistration("a", (), GenA, InA),
            ProviderRegistration("b", (), GenB, InB),
        ]
    )


def test_tempmail_is_router():
    assert issubclass(TempMail, ITempMailRouter)


def test_sticky_mode_pins_provider():
    tm = TempMail("fake", factory=_simple_factory())
    assert tm.mode is RouterMode.STICKY
    assert tm.provider == "fake"
    assert tm.create().provider == "fake"


def test_sticky_mode_requires_provider():
    with pytest.raises(BadInputError) as ei:
        TempMail(mode=RouterMode.STICKY, factory=_simple_factory())
    assert ei.value.code == "sticky_needs_provider"


def test_fallback_uses_internal_order():
    tm = TempMail(factory=_simple_factory())
    assert tm.mode is RouterMode.FALLBACK
    assert tm.provider is None
    assert tm.order == ["fake"]
    assert tm.create().provider == "fake"


def test_fallback_custom_order_and_set_order():
    factory = _two_factory(a_fails=True)
    tm = TempMail(mode="fallback", order=["a", "b"], factory=factory)
    assert tm.order == ["a", "b"]
    assert tm.create().provider == "b"

    tm.set_order(["b", "a"])
    assert tm.order == ["b", "a"]
    assert tm.create().provider == "b"


def test_fallback_one_shot_order():
    factory = _two_factory(a_fails=True)
    tm = TempMail(mode=RouterMode.FALLBACK, order=["a", "b"], factory=factory)
    assert tm.create(order=["b", "a"]).provider == "b"


def test_create_provider_arg_is_one_shot_sticky():
    factory = _two_factory()
    tm = TempMail(mode=RouterMode.FALLBACK, factory=factory)
    assert tm.create("a").provider == "a"


def test_set_mode_sticky_and_fallback():
    factory = _two_factory()
    tm = TempMail(mode=RouterMode.FALLBACK, factory=factory)
    tm.set_mode("sticky", provider="b")
    assert tm.mode is RouterMode.STICKY
    assert tm.provider == "b"
    assert tm.create().provider == "b"

    tm.set_mode(RouterMode.FALLBACK, provider="a")
    assert tm.mode is RouterMode.FALLBACK
    assert tm.order[0] == "a"


def test_empty_order_rejected():
    with pytest.raises(BadInputError):
        TempMail(mode="fallback", order=[], factory=_simple_factory())


def test_tempmail_create_list_read_delete_destroy():
    tm = TempMail("fake", factory=_simple_factory())
    assert tm.resolve("f") == "fake"
    inbox = tm.create()
    assert inbox.address == "a@fake.test"
    msgs = tm.list_messages(inbox)
    assert msgs[0]["id"] == "1"
    assert tm.read_message(inbox, msgs[0]) == "body:1"
    tm.delete_message(inbox, "1")
    tm.destroy(inbox)


def test_tempmail_wait_for_message():
    tm = TempMail("fake", factory=_simple_factory())
    msg = tm.wait_for_message(tm.create(), timeout_secs=1, poll_every=0.01)
    assert msg["id"] == "1"


def test_tempmail_wait_for_message_timeout():
    class EmptyInbox(_Inbox):
        def list_messages(self, inbox: TempInbox) -> list[dict]:
            return []

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), _Gen, EmptyInbox)]
    )
    tm = TempMail("fake", factory=factory)
    with pytest.raises(VerifyTimeoutError):
        tm.wait_for_message(tm.create(), timeout_secs=0.05, poll_every=0.02)


def test_tempmail_unknown_provider():
    tm = TempMail(factory=_simple_factory())
    with pytest.raises(UnknownProviderError):
        tm.create("nope")


def test_tempmail_unsupported_get_message():
    tm = TempMail("fake", factory=_simple_factory())
    with pytest.raises(UnprocessableError) as ei:
        tm.get_message(tm.create(), "1")
    assert ei.value.code == "get_message_unsupported"


def test_default_order_constant():
    assert TempMail.DEFAULT_ORDER
    assert TempMail.default_order() == list(TempMail.DEFAULT_ORDER)
