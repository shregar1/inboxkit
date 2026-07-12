"""Provider factory — constructs generate/inbox services and ProviderSpecs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence, Type

from inboxkit.errors import UnknownProviderError
from inboxkit.factories.abstraction import IProviderFactory
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)
from inboxkit.services.providers.spec import ProviderSpec


@dataclass(frozen=True)
class ProviderRegistration:
    """One provider's construction recipe for the factory."""

    canonical: str
    aliases: tuple[str, ...]
    generate_cls: Type[IProviderGenerateService]
    inbox_cls: Type[IProviderInboxService]


def default_registrations() -> list[ProviderRegistration]:
    """Lazy imports — keeps factory module light at import time."""
    from inboxkit.services.providers.guerrillamail.generate import (
        GuerrillaMailGenerateService,
    )
    from inboxkit.services.providers.guerrillamail.inbox import GuerrillaMailInboxService
    from inboxkit.services.providers.maildrop.generate import MailDropGenerateService
    from inboxkit.services.providers.maildrop.inbox import MailDropInboxService
    from inboxkit.services.providers.mailtm.generate import MailTmGenerateService
    from inboxkit.services.providers.mailtm.inbox import MailTmInboxService
    from inboxkit.services.providers.secmail.generate import SecMailGenerateService
    from inboxkit.services.providers.secmail.inbox import SecMailInboxService
    from inboxkit.services.providers.smailpro.generate import SmailProGenerateService
    from inboxkit.services.providers.smailpro.inbox import SmailProInboxService
    from inboxkit.services.providers.temp_mail_app.generate import (
        TempMailAppGenerateService,
    )
    from inboxkit.services.providers.temp_mail_app.inbox import TempMailAppInboxService
    from inboxkit.services.providers.temp_mail_org.generate import (
        TempMailOrgGenerateService,
    )
    from inboxkit.services.providers.temp_mail_org.inbox import TempMailOrgInboxService
    from inboxkit.services.providers.tempail.generate import TempailGenerateService
    from inboxkit.services.providers.tempail.inbox import TempailInboxService
    from inboxkit.services.providers.tempmail_lol.generate import (
        TempMailLolGenerateService,
    )
    from inboxkit.services.providers.tempmail_lol.inbox import TempMailLolInboxService
    from inboxkit.services.providers.tempmail_net.generate import (
        TempmailNetGenerateService,
    )
    from inboxkit.services.providers.tempmail_net.inbox import TempmailNetInboxService
    from inboxkit.services.providers.tempy.generate import TempyGenerateService
    from inboxkit.services.providers.tempy.inbox import TempyInboxService

    return [
        ProviderRegistration(
            "temp-mail.org",
            (
                "temp-mail.io",
                "tempmail.io",
                "tempmailio",
                "tempmail.org",
                "tempmailorg",
            ),
            TempMailOrgGenerateService,
            TempMailOrgInboxService,
        ),
        ProviderRegistration(
            "tempail",
            ("tempail.com",),
            TempailGenerateService,
            TempailInboxService,
        ),
        ProviderRegistration(
            "tempmail.net",
            ("tempmailnet",),
            TempmailNetGenerateService,
            TempmailNetInboxService,
        ),
        ProviderRegistration(
            "guerrillamail",
            ("guerrilla",),
            GuerrillaMailGenerateService,
            GuerrillaMailInboxService,
        ),
        ProviderRegistration(
            "mail.tm",
            ("mailtm",),
            MailTmGenerateService,
            MailTmInboxService,
        ),
        ProviderRegistration(
            "maildrop",
            (),
            MailDropGenerateService,
            MailDropInboxService,
        ),
        ProviderRegistration(
            "tempy.email",
            ("tempy",),
            TempyGenerateService,
            TempyInboxService,
        ),
        ProviderRegistration(
            "tempmail.lol",
            ("tempmail-lol",),
            TempMailLolGenerateService,
            TempMailLolInboxService,
        ),
        ProviderRegistration(
            "temp-mail.app",
            ("tempmailapp",),
            TempMailAppGenerateService,
            TempMailAppInboxService,
        ),
        ProviderRegistration(
            "1secmail",
            ("secmail",),
            SecMailGenerateService,
            SecMailInboxService,
        ),
        ProviderRegistration(
            "smailpro",
            ("smailpro.com", "sonjj", "temp-gmail"),
            SmailProGenerateService,
            SmailProInboxService,
        ),
    ]


class ProviderFactory(IProviderFactory):
    """Factory for disposable-mail provider services and specs (OCP/DIP)."""

    def __init__(
        self,
        registrations: Sequence[ProviderRegistration] | None = None,
        *,
        generate_builder: Callable[[Type[IProviderGenerateService], dict[str, Any]], IProviderGenerateService]
        | None = None,
        inbox_builder: Callable[[Type[IProviderInboxService], dict[str, Any]], IProviderInboxService]
        | None = None,
    ) -> None:
        regs = list(registrations) if registrations is not None else default_registrations()
        self._order: list[str] = []
        self._by_name: dict[str, ProviderRegistration] = {}
        for reg in regs:
            self._order.append(reg.canonical)
            for n in (reg.canonical, *reg.aliases):
                key = n.strip().lower()
                if key:
                    self._by_name[key] = reg
        self._generate_builder = generate_builder or (
            lambda cls, kw: cls(**kw)
        )
        self._inbox_builder = inbox_builder or (lambda cls, kw: cls(**kw))

    @classmethod
    def default(cls) -> ProviderFactory:
        return cls()

    def _lookup(self, name: str) -> ProviderRegistration:
        key = (name or "").strip().lower()
        reg = self._by_name.get(key)
        if reg is None:
            raise UnknownProviderError(
                f"unknown provider {name!r}; choose from: {', '.join(self._order)}",
                code="unknown_provider",
                details={"provider": name},
            )
        return reg

    def resolve(self, name: str) -> str:
        return self._lookup(name).canonical

    def list_names(self) -> list[str]:
        return list(self._order)

    def create_generate(self, name: str, **kwargs: Any) -> IProviderGenerateService:
        reg = self._lookup(name)
        return self._generate_builder(reg.generate_cls, kwargs)

    def create_inbox(self, name: str, **kwargs: Any) -> IProviderInboxService:
        reg = self._lookup(name)
        return self._inbox_builder(reg.inbox_cls, kwargs)

    def create_spec(self, name: str, **kwargs: Any) -> ProviderSpec:
        reg = self._lookup(name)
        generate = self.create_generate(name, **kwargs)
        return ProviderSpec(reg.canonical, reg.aliases, generate)

    def create_specs(self, **kwargs: Any) -> list[ProviderSpec]:
        return [self.create_spec(canonical, **kwargs) for canonical in self._order]
