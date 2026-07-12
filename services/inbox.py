"""Create / poll disposable inboxes across providers."""

from __future__ import annotations

from typing import Callable, Mapping, Sequence

from inboxkit.abstractions import IService
from inboxkit.errors import (
    AllProvidersFailedError,
    UnknownProviderError,
    VerifyTimeoutError,
)
from inboxkit.models import TempInbox
from inboxkit.services.providers.registry import (
    DEFAULT_PROVIDER_ORDER,
    ProviderSpec,
    default_provider_specs,
)
from inboxkit.factories import ProviderFactory
from inboxkit.utilities import VerifyUtility

# Re-export for callers that imported order from this module.
PROVIDER_ORDER = DEFAULT_PROVIDER_ORDER


def _build_minter_map(
    specs: Sequence[ProviderSpec],
) -> dict[str, Callable[[], TempInbox]]:
    out: dict[str, Callable[[], TempInbox]] = {}
    for spec in specs:
        mint = spec.generate.mint
        for name in spec.all_names():
            out[name] = mint
    return out


class InboxService(IService):
    """Orchestrates provider minting and verify-link polling.

    Depends on abstractions (``ProviderSpec`` / ``ProviderFactory``), not
    concrete provider modules — pass ``specs`` or ``factory`` in tests (DIP).
    """

    def __init__(
        self,
        *,
        specs: Sequence[ProviderSpec] | None = None,
        factory: ProviderFactory | None = None,
        order: Sequence[str] | None = None,
        extract_link: Callable[[str], str | None] = VerifyUtility.extract_link,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        import time

        if specs is not None:
            self._specs = list(specs)
        elif factory is not None:
            self._specs = factory.create_specs()
        else:
            self._specs = default_provider_specs()
        self._order = list(order) if order is not None else [
            s.canonical for s in self._specs
        ]
        self._minters: Mapping[str, Callable[[], TempInbox]] = _build_minter_map(
            self._specs
        )
        self._extract_link = extract_link
        self._sleep = sleep or time.sleep
        self._clock = clock or time.time

    def list_providers(self) -> list[str]:
        return list(self._order)

    def create_inbox(
        self,
        provider: str | None = None,
        *,
        providers: Sequence[str] | None = None,
    ) -> TempInbox:
        name = (provider or "auto").strip().lower()
        if name in ("auto", "any", ""):
            order = list(providers) if providers else list(self._order)
            errors: list[str] = []
            for p in order:
                key = p.strip().lower()
                mint_fn = self._minters.get(key)
                if not mint_fn:
                    errors.append(f"{p}: unknown")
                    continue
                try:
                    return mint_fn()
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{p}: {e}")
            raise AllProvidersFailedError(
                "all tempmail providers failed:\n  " + "\n  ".join(errors),
                code="all_providers_failed",
                details={"errors": errors},
            )

        mint_fn = self._minters.get(name)
        if not mint_fn:
            raise UnknownProviderError(
                f"unknown provider {provider!r}; choose from: {', '.join(self._order)}",
                code="unknown_provider",
                details={"provider": provider},
            )
        return mint_fn()

    def poll_verify_link(
        self,
        inbox: TempInbox,
        *,
        timeout_secs: float = 180,
        poll_every: float = 5,
    ) -> str:
        deadline = self._clock() + timeout_secs
        seen: set[str] = set()

        while self._clock() < deadline:
            try:
                for msg in inbox.list_messages():
                    mid = str(msg.get("id") or msg.get("mail_id") or "")
                    if mid and mid in seen:
                        continue
                    if mid:
                        seen.add(mid)
                    body = inbox.read_message(msg)
                    link = self._extract_link(body)
                    if link:
                        return link
            except Exception:  # noqa: BLE001
                pass
            self._sleep(poll_every)

        raise VerifyTimeoutError(
            f"No verify link in {inbox.address} "
            f"({inbox.provider}) within {timeout_secs}s",
            code="verify_timeout",
            details={
                "address": inbox.address,
                "provider": inbox.provider,
                "timeout_secs": timeout_secs,
            },
        )


_DEFAULT = InboxService()


def list_providers() -> list[str]:
    return _DEFAULT.list_providers()


def create_inbox(
    provider: str | None = None,
    *,
    providers: Sequence[str] | None = None,
) -> TempInbox:
    return _DEFAULT.create_inbox(provider, providers=providers)


def poll_verify_link(
    inbox: TempInbox,
    *,
    timeout_secs: float = 180,
    poll_every: float = 5,
) -> str:
    return _DEFAULT.poll_verify_link(
        inbox, timeout_secs=timeout_secs, poll_every=poll_every
    )
