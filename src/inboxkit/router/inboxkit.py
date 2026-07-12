"""Public-facing InboxKit router — sticky or fallback provider selection."""

from __future__ import annotations

from typing import Any, Callable, Sequence

from inboxkit.constants import PROVIDER_ORDER
from inboxkit.enums import RouterMode
from inboxkit.errors import (
    BadInputError,
    InboxNotBoundError,
    UnprocessableError,
    VerifyTimeoutError,
)
from inboxkit.factories import ProviderFactory
from inboxkit.models import TempInbox
from inboxkit.router.abstraction import IInboxKitRouter
from inboxkit.services.inbox import InboxService
from inboxkit.services.providers.abstraction import (
    IProviderGenerateService,
    IProviderInboxService,
)
from inboxkit.utilities import VerifyUtility

# Common destroy method names across generate services (first match wins).
_DESTROY_METHODS = (
    "destroy_mailbox",
    "delete_email",
    "delete_account",
    "delete_mailbox",
    "forget_me",
)

# Common single-message delete names on inbox services.
_DELETE_MESSAGE_METHODS = (
    "delete_message",
    "delete_messages",
    "remove_gmail_message",
)


class InboxKit(IInboxKitRouter):
    """Common router for disposable-email operations.

    Two modes
    ---------
    sticky
        User selected one provider. Only that provider is used — no fallback.
    fallback
        Try providers in ``order`` (user-supplied) or the internal
        ``DEFAULT_ORDER`` until one mint succeeds.

    Mode is inferred when omitted:
      - concrete ``provider`` → sticky
      - no provider / ``\"auto\"`` → fallback

    Examples::

        from inboxkit import InboxKit, RouterMode

        # sticky — only mail.tm
        tm = InboxKit("mail.tm")
        inbox = tm.create()

        # fallback — internal default order
        tm = InboxKit()
        inbox = tm.create()

        # fallback — custom order
        tm = InboxKit(mode=RouterMode.FALLBACK, order=["tempmail.net", "mail.tm", "1secmail"])
        inbox = tm.create()

        # change order later
        tm.set_order(["guerrillamail", "maildrop"])
    """

    # Internal default try-order for fallback mode (canonical names).
    DEFAULT_ORDER: tuple[str, ...] = tuple(PROVIDER_ORDER)

    def __init__(
        self,
        provider: str | None = None,
        *,
        mode: RouterMode | str | None = None,
        order: Sequence[str] | None = None,
        factory: ProviderFactory | None = None,
        extract_link: Callable[[str], str | None] = VerifyUtility.extract_link,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
        **provider_kwargs: Any,
    ) -> None:
        self._factory = factory or ProviderFactory.default()
        self._kwargs = dict(provider_kwargs)

        raw = (provider or "").strip().lower()
        inferred = (
            RouterMode.STICKY
            if raw and raw not in ("auto", "any")
            else RouterMode.FALLBACK
        )
        resolved_mode = RouterMode.coerce(mode) if mode is not None else inferred
        if resolved_mode is None:
            raise BadInputError(
                f"unknown mode {mode!r}; use 'sticky' or 'fallback'",
                code="unknown_mode",
                details={"mode": mode},
            )
        self._mode = resolved_mode

        if self._mode is RouterMode.STICKY:
            if not raw or raw in ("auto", "any"):
                raise BadInputError(
                    "sticky mode requires a concrete provider name",
                    code="sticky_needs_provider",
                )
            self._sticky_provider = self._factory.resolve(raw)
        else:
            self._sticky_provider = None
            if raw and raw not in ("auto", "any"):
                # Explicit fallback mode but a provider was passed — treat as
                # preferred first entry unless custom order already set.
                if order is None:
                    order = (raw, *self._default_order_for_factory())

        if order is not None:
            self._order = self._normalize_order(order)
        else:
            self._order = self._default_order_for_factory()

        specs = (
            self._factory.create_specs(**self._kwargs) if self._kwargs else None
        )
        self._svc = InboxService(
            factory=self._factory if specs is None else None,
            specs=specs,
            order=self._order,
            extract_link=extract_link,
            sleep=sleep,
            clock=clock,
        )
        self._extract_link = extract_link
        self._sleep = self._svc._sleep
        self._clock = self._svc._clock

    # --- mode / order ------------------------------------------------------

    @classmethod
    def default_order(cls) -> list[str]:
        """Copy of the package-internal fallback provider order."""
        return list(cls.DEFAULT_ORDER)

    @property
    def mode(self) -> RouterMode:
        return self._mode

    @property
    def provider(self) -> str | None:
        """Pinned provider in sticky mode; ``None`` in fallback mode."""
        return self._sticky_provider

    @property
    def order(self) -> list[str]:
        """Canonical provider try-order (used by fallback mode)."""
        return list(self._order)

    @property
    def factory(self) -> ProviderFactory:
        return self._factory

    def set_mode(
        self,
        mode: RouterMode | str,
        *,
        provider: str | None = None,
    ) -> InboxKit:
        """Switch between sticky and fallback.

        Sticky requires ``provider`` (or an already pinned sticky provider).
        """
        resolved = RouterMode.coerce(mode)
        if resolved is None:
            raise BadInputError(
                f"unknown mode {mode!r}; use 'sticky' or 'fallback'",
                code="unknown_mode",
                details={"mode": mode},
            )
        if resolved is RouterMode.STICKY:
            name = provider or self._sticky_provider
            if not name:
                raise BadInputError(
                    "sticky mode requires provider=...",
                    code="sticky_needs_provider",
                )
            self._sticky_provider = self._factory.resolve(name)
        else:
            if provider:
                # Prefer this provider first in fallback order.
                preferred = self._factory.resolve(provider)
                rest = [p for p in self._order if p != preferred]
                self._order = [preferred, *rest]
                self._svc._order = list(self._order)
            self._sticky_provider = None
        self._mode = resolved
        return self

    def set_order(self, order: Sequence[str]) -> InboxKit:
        """Set fallback try-order (aliases resolved; empty raises)."""
        self._order = self._normalize_order(order)
        self._svc._order = list(self._order)
        return self

    def providers(self) -> list[str]:
        """Providers available from the factory (registration order)."""
        return self._factory.list_names()

    def resolve(self, provider: str) -> str:
        """Canonical name for a provider / alias."""
        name = (provider or "").strip().lower()
        if not name or name in ("auto", "any"):
            raise UnprocessableError(
                "cannot resolve canonical name for provider='auto'",
                code="auto_not_resolvable",
            )
        return self._factory.resolve(name)

    # --- services ----------------------------------------------------------

    def generate(
        self, provider: str | None = None, **kwargs: Any
    ) -> IProviderGenerateService:
        """Raw generate service (advanced / SDK escape hatch)."""
        name = self._require_concrete(provider)
        kw = {**self._kwargs, **kwargs}
        return self._factory.create_generate(name, **kw)

    def inbox_service(
        self, provider: str | None = None, **kwargs: Any
    ) -> IProviderInboxService:
        """Raw inbox service (advanced / SDK escape hatch)."""
        name = self._require_concrete(provider)
        kw = {**self._kwargs, **kwargs}
        return self._factory.create_inbox(name, **kw)

    def create(
        self,
        provider: str | None = None,
        *,
        order: Sequence[str] | None = None,
    ) -> TempInbox:
        """Mint an inbox and return full access details.

        Returns a :class:`~tempmail.models.TempInbox` with:

        - ``email`` / ``address`` — generated address
        - ``token`` / ``password`` / ``credentials`` — auth to read the inbox
        - ``meta`` / ``to_dict()`` — every provider-specific detail

        Example::

            inbox = tm.create()
            print(inbox.email, inbox.credentials)
            print(inbox.to_dict())  # full snapshot
        """
        if provider is not None:
            return self.generate(provider).mint()

        if self._mode is RouterMode.STICKY:
            assert self._sticky_provider is not None
            return self.generate(self._sticky_provider).mint()

        try_order = (
            self._normalize_order(order) if order is not None else list(self._order)
        )
        return self._svc.create_inbox("auto", providers=try_order)

    def list_messages(self, inbox: TempInbox) -> list[dict[str, Any]]:
        try:
            return inbox.list_messages()
        except InboxNotBoundError:
            return self._inbox_for(inbox).list_messages(inbox)

    def read_message(self, inbox: TempInbox, msg: dict[str, Any]) -> str:
        try:
            return inbox.read_message(msg)
        except InboxNotBoundError:
            return self._inbox_for(inbox).read_message(inbox, msg)

    def get_message(
        self, inbox: TempInbox, message_id: str | int, **kwargs: Any
    ) -> Any:
        """Fetch full message when the provider exposes ``get_message``."""
        svc = self._inbox_for(inbox)
        fn = getattr(svc, "get_message", None)
        if not callable(fn):
            raise UnprocessableError(
                f"{inbox.provider}: get_message is not supported",
                code="get_message_unsupported",
                details={"provider": inbox.provider},
            )
        return fn(inbox, message_id, **kwargs)

    def delete_message(
        self,
        inbox: TempInbox,
        message_id: str | int,
        **kwargs: Any,
    ) -> Any:
        svc = self._inbox_for(inbox)
        for name in _DELETE_MESSAGE_METHODS:
            fn = getattr(svc, name, None)
            if not callable(fn):
                continue
            if name == "delete_messages":
                return fn(inbox, [message_id], **kwargs)
            return fn(inbox, message_id, **kwargs)
        raise UnprocessableError(
            f"{inbox.provider}: delete_message is not supported",
            code="delete_message_unsupported",
            details={"provider": inbox.provider},
        )

    def destroy(self, inbox: TempInbox, **kwargs: Any) -> Any:
        gen = self._factory.create_generate(inbox.provider, **self._kwargs)
        for name in _DESTROY_METHODS:
            fn = getattr(gen, name, None)
            if not callable(fn):
                continue
            if name == "delete_mailbox":
                return fn(inbox.address, **kwargs)
            if name == "delete_account":
                return fn(inbox, kwargs.pop("account_id", None), **kwargs)
            return fn(inbox, **kwargs)
        raise UnprocessableError(
            f"{inbox.provider}: destroy / delete mailbox is not supported",
            code="destroy_unsupported",
            details={"provider": inbox.provider},
        )

    def wait_for_message(
        self,
        inbox: TempInbox,
        *,
        timeout_secs: float = 120,
        poll_every: float = 5,
    ) -> dict[str, Any]:
        deadline = self._clock() + timeout_secs
        seen: set[str] = set()
        while self._clock() < deadline:
            try:
                msgs = self.list_messages(inbox)
            except Exception:  # noqa: BLE001
                msgs = []
            for msg in msgs:
                mid = str(msg.get("id") or msg.get("mail_id") or "")
                if mid and mid in seen:
                    continue
                if mid:
                    seen.add(mid)
                return msg
            if msgs:
                return msgs[0]
            self._sleep(poll_every)
        raise VerifyTimeoutError(
            f"No message in {inbox.address} ({inbox.provider}) "
            f"within {timeout_secs}s",
            code="wait_message_timeout",
            details={
                "address": inbox.address,
                "provider": inbox.provider,
                "timeout_secs": timeout_secs,
            },
        )

    def wait_for_link(
        self,
        inbox: TempInbox,
        *,
        timeout_secs: float = 180,
        poll_every: float = 5,
    ) -> str:
        return self._svc.poll_verify_link(
            inbox, timeout_secs=timeout_secs, poll_every=poll_every
        )

    # --- internals ---------------------------------------------------------

    def _default_order_for_factory(self) -> list[str]:
        """Internal order = package DEFAULT_ORDER ∩ factory, then extras."""
        available = set(self._factory.list_names())
        ordered = [p for p in self.DEFAULT_ORDER if p in available]
        for p in self._factory.list_names():
            if p not in ordered:
                ordered.append(p)
        return ordered

    def _normalize_order(self, order: Sequence[str]) -> list[str]:
        if not order:
            raise BadInputError(
                "provider order must not be empty",
                code="empty_provider_order",
            )
        out: list[str] = []
        seen: set[str] = set()
        for raw in order:
            canonical = self._factory.resolve(str(raw).strip().lower())
            if canonical not in seen:
                seen.add(canonical)
                out.append(canonical)
        return out

    def _require_concrete(self, provider: str | None) -> str:
        if provider is not None:
            return self.resolve(provider)
        if self._mode is RouterMode.STICKY and self._sticky_provider:
            return self._sticky_provider
        raise UnprocessableError(
            "provider name required in fallback mode; "
            f"choose from: {', '.join(self.providers())}",
            code="provider_required",
        )

    def _inbox_for(self, inbox: TempInbox) -> IProviderInboxService:
        return self._factory.create_inbox(inbox.provider, **self._kwargs)
