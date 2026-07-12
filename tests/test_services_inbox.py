"""InboxService module-level and edge-path coverage."""

from __future__ import annotations

import pytest

from inboxkit.errors import AllProvidersFailedError, UnknownProviderError, VerifyTimeoutError
from inboxkit.models import TempInbox
from inboxkit.services import inbox as inbox_mod
from inboxkit.services.inbox import InboxService
from inboxkit.services.providers.spec import ProviderSpec
from inboxkit.services.providers.abstraction import IProviderGenerateService


class _Gen(IProviderGenerateService):
    def __init__(self, name: str = "ok", fail: bool = False) -> None:
        self._name = name
        self._fail = fail

    @property
    def provider_name(self) -> str:
        return self._name

    def mint(self) -> TempInbox:
        if self._fail:
            raise RuntimeError("mint-fail")
        return TempInbox(
            address=f"a@{self._name}.test",
            provider=self._name,
            token="t",
            _list=lambda self: [{"id": "1"}],
            _read=lambda self, msg: "https://example.com/verify?token=zz",
        )


def test_create_inbox_auto_unknown_and_all_failed():
    ok = ProviderSpec("ok", (), _Gen())
    bad = ProviderSpec("bad", (), _Gen("bad", fail=True))
    svc = InboxService(specs=[ok, bad], order=["bad", "missing", "ok"])
    assert svc.list_providers() == ["bad", "missing", "ok"]
    inbox = svc.create_inbox("auto")
    assert inbox.provider == "ok"

    only_bad = InboxService(specs=[bad], order=["bad", "nope"])
    with pytest.raises(AllProvidersFailedError) as ei:
        only_bad.create_inbox("auto")
    assert "unknown" in str(ei.value) or "mint-fail" in str(ei.value)

    with pytest.raises(UnknownProviderError):
        svc.create_inbox("nope")

    assert svc.create_inbox("ok").provider == "ok"


def test_poll_verify_link_success_skip_seen_and_errors():
    calls = {"n": 0}

    def _list(self):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        if calls["n"] == 2:
            return [{"id": "1"}]  # no link
        if calls["n"] == 3:
            return [{"id": "1"}, {"id": "2"}]  # skip seen 1
        return [{"id": "2"}]

    def _read(self, msg):
        if msg.get("id") == "1":
            return "no link here"
        return "go https://example.com/verify?token=ok"

    inbox = TempInbox(
        address="a@ok.test",
        provider="ok",
        token="t",
        _list=_list,
        _read=_read,
    )
    clock = {"t": 0.0}
    svc = InboxService(
        specs=[ProviderSpec("ok", (), _Gen())],
        clock=lambda: clock["t"],
        sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
    )
    link = svc.poll_verify_link(inbox, timeout_secs=20, poll_every=1)
    assert "token=ok" in link


def test_poll_verify_timeout():
    inbox = TempInbox(
        address="a@ok.test",
        provider="ok",
        token="t",
        _list=lambda self: [],
        _read=lambda self, msg: "",
    )
    t = {"v": 0.0}
    svc = InboxService(
        specs=[ProviderSpec("ok", (), _Gen())],
        clock=lambda: t["v"],
        sleep=lambda s: t.__setitem__("v", t["v"] + s),
    )
    with pytest.raises(VerifyTimeoutError):
        svc.poll_verify_link(inbox, timeout_secs=0.05, poll_every=0.02)


def test_module_level_wrappers(monkeypatch):
    inbox = TempInbox(
        address="a@x.test",
        provider="x",
        token="t",
        _list=lambda self: [{"id": "1"}],
        _read=lambda self, msg: "https://example.com/verify?token=m",
    )

    class Stub:
        def list_providers(self):
            return ["stub"]

        def create_inbox(self, provider=None, providers=None):
            return inbox

        def poll_verify_link(self, inbox, timeout_secs=180, poll_every=5):
            return "https://example.com/verify?token=m"

    monkeypatch.setattr(inbox_mod, "_DEFAULT", Stub())
    assert inbox_mod.list_providers() == ["stub"]
    assert inbox_mod.create_inbox("x") is inbox
    assert "token=m" in inbox_mod.poll_verify_link(inbox)
