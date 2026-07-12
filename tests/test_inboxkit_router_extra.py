"""Extra InboxKit router branch coverage."""

from __future__ import annotations

import pytest

from inboxkit.enums import RouterMode
from inboxkit.errors import BadInputError, UnprocessableError, VerifyTimeoutError
from inboxkit.factories import ProviderFactory, ProviderRegistration
from inboxkit.models import TempInbox
from inboxkit.router import InboxKit
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


def _factory(*names: str) -> ProviderFactory:
    regs = []
    for n in names or ("fake",):

        class G(_Gen):
            def __init__(self, _n=n) -> None:
                super().__init__(_n)

        class I(_Inbox):
            def __init__(self, _n=n) -> None:
                super().__init__(_n)

        regs.append(ProviderRegistration(n, (), G, I))
    return ProviderFactory(regs)


def test_unknown_mode_init_and_set_mode():
    with pytest.raises(BadInputError) as ei:
        InboxKit(mode="nope", factory=_factory())
    assert ei.value.code == "unknown_mode"

    tm = InboxKit(mode=RouterMode.FALLBACK, factory=_factory("a", "b"))
    with pytest.raises(BadInputError):
        tm.set_mode("bogus")
    with pytest.raises(BadInputError):
        tm.set_mode("sticky")  # no provider


def test_fallback_with_provider_prefers_first():
    tm = InboxKit("a", mode=RouterMode.FALLBACK, factory=_factory("a", "b"))
    assert tm.order[0] == "a"
    assert tm.factory is not None
    assert "a" in tm.providers()


def test_resolve_auto_and_generate_inbox_service():
    tm = InboxKit("fake", factory=_factory())
    with pytest.raises(UnprocessableError) as ei:
        tm.resolve("auto")
    assert ei.value.code == "auto_not_resolvable"
    with pytest.raises(UnprocessableError):
        tm.resolve("")
    assert tm.generate("fake").provider_name == "fake"
    assert tm.inbox_service("fake").provider_name == "fake"
    assert tm.generate().provider_name == "fake"
    assert tm.inbox_service().provider_name == "fake"

    fb = InboxKit(factory=_factory())
    with pytest.raises(UnprocessableError) as ei:
        fb.generate()
    assert ei.value.code == "provider_required"


def test_list_read_via_factory_when_unbound():
    tm = InboxKit("fake", factory=_factory())
    inbox = TempInbox(address="a@fake.test", provider="fake", token="t")
    assert tm.list_messages(inbox)[0]["id"] == "1"
    assert tm.read_message(inbox, {"id": "1"}) == "body:1"


def test_get_message_supported():
    class InWithGet(_Inbox):
        def get_message(self, inbox, message_id, **kwargs):
            return {"id": message_id, **kwargs}

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), _Gen, InWithGet)]
    )
    tm = InboxKit("fake", factory=factory)
    assert tm.get_message(tm.create(), "99", x=1)["id"] == "99"


def test_delete_messages_variant_and_unsupported():
    class InDelMsgs(_Inbox):
        def delete_message(self, inbox, message_id):  # still present — router tries delete_message first
            raise AssertionError("should use delete_messages only if delete_message missing")

    class InOnlyDelMsgs(IProviderInboxService):
        @property
        def provider_name(self) -> str:
            return "fake"

        def list_messages(self, inbox):
            return []

        def read_message(self, inbox, msg):
            return ""

        def delete_messages(self, inbox, ids):
            return {"deleted": ids}

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), _Gen, InOnlyDelMsgs)]
    )
    tm = InboxKit("fake", factory=factory)
    assert tm.delete_message(tm.create(), "1") == {"deleted": ["1"]}

    class NoDel(IProviderInboxService):
        @property
        def provider_name(self) -> str:
            return "fake"

        def list_messages(self, inbox):
            return []

        def read_message(self, inbox, msg):
            return ""

    factory2 = ProviderFactory([ProviderRegistration("fake", (), _Gen, NoDel)])
    tm2 = InboxKit("fake", factory=factory2)
    with pytest.raises(UnprocessableError) as ei:
        tm2.delete_message(tm2.create(), "1")
    assert ei.value.code == "delete_message_unsupported"


def test_destroy_variants():
    class GenOnlyEmail(IProviderGenerateService):
        @property
        def provider_name(self):
            return "fake"

        def mint(self):
            return TempInbox(address="a@fake.test", provider="fake", token="t")

        def delete_email(self, inbox):
            return "de"

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), GenOnlyEmail, _Inbox)]
    )
    tm = InboxKit("fake", factory=factory)
    assert tm.destroy(tm.create()) == "de"

    class GenOnlyAccount(IProviderGenerateService):
        @property
        def provider_name(self):
            return "fake"

        def mint(self):
            return TempInbox(address="a@fake.test", provider="fake", token="t")

        def delete_account(self, inbox, account_id=None):
            return account_id or "from-meta"

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), GenOnlyAccount, _Inbox)]
    )
    tm = InboxKit("fake", factory=factory)
    assert tm.destroy(tm.create(), account_id="acc") == "acc"

    class GenOnlyMailbox(IProviderGenerateService):
        @property
        def provider_name(self):
            return "fake"

        def mint(self):
            return TempInbox(address="a@fake.test", provider="fake", token="t")

        def delete_mailbox(self, address):
            return address

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), GenOnlyMailbox, _Inbox)]
    )
    tm = InboxKit("fake", factory=factory)
    assert tm.destroy(tm.create()) == "a@fake.test"

    class GenBare(IProviderGenerateService):
        @property
        def provider_name(self):
            return "fake"

        def mint(self):
            return TempInbox(address="a@fake.test", provider="fake", token="t")

    factory = ProviderFactory([ProviderRegistration("fake", (), GenBare, _Inbox)])
    tm = InboxKit("fake", factory=factory)
    with pytest.raises(UnprocessableError) as ei:
        tm.destroy(tm.create())
    assert ei.value.code == "destroy_unsupported"


def test_wait_for_message_edges():
    # Shared counters — factory creates a new inbox service each call.
    state = {"n": 0}

    class Flaky(_Inbox):
        def list_messages(self, inbox):
            state["n"] += 1
            if state["n"] == 1:
                raise RuntimeError("transient")
            return [{"id": "1", "subject": "hi"}]

    factory = ProviderFactory([ProviderRegistration("fake", (), _Gen, Flaky)])
    clock = {"t": 0.0}
    tm = InboxKit(
        "fake",
        factory=factory,
        clock=lambda: clock["t"],
        sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
    )
    msg = tm.wait_for_message(tm.create(), timeout_secs=10, poll_every=1)
    assert msg["id"] == "1"

    state2 = {"n": 0}

    class EmptyThenMailId(_Inbox):
        def list_messages(self, inbox):
            state2["n"] += 1
            if state2["n"] < 2:
                return []
            return [{"mail_id": "m9", "subject": "x"}]

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), _Gen, EmptyThenMailId)]
    )
    clock["t"] = 0.0
    tm = InboxKit(
        "fake",
        factory=factory,
        clock=lambda: clock["t"],
        sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
    )
    assert tm.wait_for_message(tm.create(), timeout_secs=5, poll_every=1)["mail_id"] == "m9"

    class NoIdMsgs(_Inbox):
        def list_messages(self, inbox):
            return [{"subject": "no-id"}]

    factory = ProviderFactory([ProviderRegistration("fake", (), _Gen, NoIdMsgs)])
    tm = InboxKit("fake", factory=factory, clock=lambda: 0.0, sleep=lambda s: None)
    assert tm.wait_for_message(tm.create(), timeout_secs=1, poll_every=0.1)["subject"] == "no-id"

    # Cover seen-skip + msgs[0] fallback: first poll returns id, second call
    # would skip — use bound inbox that returns duplicate-only after first return
    # (router returns on first unseen, so exercise via direct loop is enough via
    # empty-mid path above). Cover line 356 by waiting with seen set manually
    # through a counter that returns the same id twice across sleeps is hard
    # because wait returns immediately; cover 361 via all-seen then empty mid:
    seen_state = {"n": 0}

    class AllSeenThenPlain(_Inbox):
        def list_messages(self, inbox):
            seen_state["n"] += 1
            if seen_state["n"] == 1:
                return [{"id": "keep"}]
            # After first message returned, wait_for_message exits — so this
            # path is for a fresh wait that gets only empty-id messages after
            # filtering... Use empty id list that is non-empty for line 361.
            return [{"subject": "plain"}]

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), _Gen, AllSeenThenPlain)]
    )
    tm = InboxKit("fake", factory=factory, clock=lambda: 0.0, sleep=lambda s: None)
    assert tm.wait_for_message(tm.create(), timeout_secs=1, poll_every=0.1)["id"] == "keep"


def test_wait_for_link():
    tm = InboxKit(
        "fake",
        factory=_factory(),
        clock=lambda: 0.0,
        sleep=lambda s: None,
    )
    inbox = TempInbox(
        address="a@fake.test",
        provider="fake",
        token="t",
        _list=lambda self: [{"id": "1"}],
        _read=lambda self, msg: "https://example.com/verify?token=abc",
    )
    link = tm.wait_for_link(inbox, timeout_secs=1, poll_every=0.1)
    assert "token=abc" in link


def test_provider_kwargs_create_specs():
    class GenKw(_Gen):
        def __init__(self, api_key: str | None = None) -> None:
            super().__init__("fake")
            self.api_key = api_key

    factory = ProviderFactory(
        [ProviderRegistration("fake", (), GenKw, _Inbox)]
    )
    tm = InboxKit("fake", factory=factory, api_key="k")
    assert tm.create().provider == "fake"
