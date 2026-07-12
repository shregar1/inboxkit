"""Factory contracts for constructing providers and specs."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from inboxkit.abstractions import IFactory
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)
from inboxkit.services.providers.spec import ProviderSpec


class IProviderFactory(IFactory):
    """Creates provider generate/inbox services and ``ProviderSpec`` wiring."""

    @abstractmethod
    def resolve(self, name: str) -> str:
        """Return canonical provider name for ``name`` (or alias)."""

    @abstractmethod
    def list_names(self) -> list[str]:
        """Canonical provider names in default order."""

    @abstractmethod
    def create_generate(self, name: str, **kwargs: Any) -> IProviderGenerateService:
        """Instantiate the generate service for ``name``."""

    @abstractmethod
    def create_inbox(self, name: str, **kwargs: Any) -> IProviderInboxService:
        """Instantiate the inbox service for ``name``."""

    @abstractmethod
    def create_spec(self, name: str, **kwargs: Any) -> ProviderSpec:
        """Build a ``ProviderSpec`` (canonical + aliases + generate instance)."""

    @abstractmethod
    def create_specs(self, **kwargs: Any) -> list[ProviderSpec]:
        """Build specs for every registered provider (DIP wiring for InboxService)."""
