"""Provider wiring spec (DIP token for InboxService)."""

from __future__ import annotations

from dataclasses import dataclass

from inboxkit.services.providers.abstraction import IProviderGenerateService


@dataclass(frozen=True)
class ProviderSpec:
    """One mintable provider + aliases."""

    canonical: str
    aliases: tuple[str, ...]
    generate: IProviderGenerateService

    def all_names(self) -> tuple[str, ...]:
        names = (self.canonical, *self.aliases)
        seen: set[str] = set()
        out: list[str] = []
        for n in names:
            key = n.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(key)
        return tuple(out)
