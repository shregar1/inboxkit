"""ProviderFactory unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DOCS = Path(__file__).resolve().parents[2]
if str(_DOCS) not in sys.path:
    sys.path.insert(0, str(_DOCS))

from inboxkit.abstractions import IFactory
from inboxkit.errors import UnknownProviderError
from inboxkit.factories import (
    IProviderFactory,
    ProviderFactory,
    ProviderRegistration,
)
from inboxkit.models import TempInbox
from inboxkit.services.inbox import InboxService
from inboxkit.services.providers.abstraction import IProviderGenerateService
from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
from inboxkit.services.providers.spec import ProviderSpec


class _FakeGenerate(IProviderGenerateService):
    def __init__(self, name: str = "fake") -> None:
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def mint(self) -> TempInbox:
        return TempInbox(address="a@b.c", provider=self._name)


class _FakeInbox:
    def list_messages(self, inbox: TempInbox) -> list:
        return []

    def read_message(self, inbox: TempInbox, msg: dict) -> str:
        return ""


def test_provider_factory_is_ifactory():
    assert issubclass(ProviderFactory, IProviderFactory)
    assert issubclass(IProviderFactory, IFactory)


def test_provider_factory_resolve_and_create():
    factory = ProviderFactory.default()
    assert factory.resolve("mailtm") == "mail.tm"
    assert factory.resolve("temp-mail.io") == "temp-mail.org"
    gen = factory.create_generate("mail.tm")
    assert isinstance(gen, MailTmGenerateService)
    inbox = factory.create_inbox("mailtm")
    assert isinstance(inbox, MailTmInboxService)
    spec = factory.create_spec("guerrilla")
    assert spec.canonical == "guerrillamail"
    assert "guerrilla" in spec.all_names()


def test_provider_factory_create_specs_matches_order():
    factory = ProviderFactory.default()
    specs = factory.create_specs()
    assert [s.canonical for s in specs] == factory.list_names()
    assert "tempmail.net" in factory.list_names()
    assert "smailpro" in factory.list_names()


def test_provider_factory_unknown():
    factory = ProviderFactory.default()
    with pytest.raises(UnknownProviderError):
        factory.create_generate("nope")


def test_provider_factory_custom_registration():
    factory = ProviderFactory(
        [
            ProviderRegistration(
                "fake",
                ("f",),
                _FakeGenerate,  # type: ignore[arg-type]
                _FakeInbox,  # type: ignore[arg-type]
            )
        ]
    )
    assert factory.resolve("f") == "fake"
    gen = factory.create_generate("f")
    assert gen.mint().provider == "fake"
    svc = InboxService(factory=factory)
    assert svc.list_providers() == ["fake"]
    assert svc.create_inbox("f").address == "a@b.c"


def test_provider_spec_still_exported_from_registry():
    from inboxkit.services.providers.registry import ProviderSpec as RegSpec
    from inboxkit.services.providers.registry import default_provider_specs

    assert RegSpec is ProviderSpec
    specs = default_provider_specs()
    assert specs
    assert all(isinstance(s, ProviderSpec) for s in specs)
