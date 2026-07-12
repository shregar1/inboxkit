"""Agent-oriented usage handbook for inboxkit.

Print or fetch this when an AI agent (or human) is new to the package::

    python -m inboxkit docs
    inboxkit docs

    from inboxkit import docs
    print(docs())
"""

from __future__ import annotations

from typing import TextIO

# Lazy imports inside docs() keep ``python -m inboxkit --help`` light and avoid
# circular imports at package import time when only docs is needed.


def docs(*, include_providers: bool = True) -> str:
    """Return the full agent handover guide as a single markdown string."""
    from inboxkit import __version__
    from inboxkit.router.tempmail import TempMail

    order = ", ".join(TempMail.DEFAULT_ORDER)
    providers = "\n".join(f"  - `{name}`" for name in TempMail.DEFAULT_ORDER)

    provider_block = ""
    if include_providers:
        provider_block = f"""
## Providers (default fallback order)

{providers}

Aliases are accepted (e.g. `mailtm` → `mail.tm`, `secmail` → `1secmail`).
"""

    return f"""# inboxkit agent handover guide (v{__version__})

You are using **inboxkit** — a stdlib-only Python library that mints disposable
email inboxes across multiple providers through one router: `TempMail`.

**Install:** `pip install git+https://github.com/shregar1/inboxkit.git`
**Re-read this guide anytime:** `python -m inboxkit docs` or `from inboxkit import docs; print(docs())`

## Rules of thumb

1. Prefer `from inboxkit import TempMail` for almost all work.
2. Pass a provider name → **sticky** (that provider only, no fallback).
3. Pass nothing / `mode="fallback"` → try providers in order until mint works.
4. `create()` returns a `TempInbox` with `email`, `token`, `credentials`, `meta`.
5. Never put banking / 2FA / recovery / secrets in disposable mail.
6. Some providers need env keys: `SMAILPRO_API_KEY`, `TEMP_MAIL_API_KEY`.
7. Site scrapers can hit captchas — switch provider or use fallback order.
8. No third-party HTTP libs required (`urllib` only).

## Minimal sticky example

```python
from inboxkit import TempMail

tm = TempMail("mail.tm")
inbox = tm.create()
print(inbox.email)
print(inbox.credentials)   # auth needed to read this mailbox again
print(inbox.to_dict())     # full snapshot
```

## Minimal fallback example

```python
from inboxkit import TempMail, RouterMode

tm = TempMail()  # DEFAULT_ORDER
inbox = tm.create()

tm = TempMail(
    mode=RouterMode.FALLBACK,
    order=["tempmail.net", "mail.tm", "1secmail", "guerrillamail"],
)
inbox = tm.create()
print(inbox.email, "via", inbox.provider)
```

## Signup / verify-link recipe (most common agent task)

```python
from inboxkit import TempMail

tm = TempMail("mail.tm")
inbox = tm.create()
email = inbox.email
# → submit `email` to the target site (signup, magic link, reset, …)

msg = tm.wait_for_message(inbox, timeout_secs=120)
body = tm.read_message(inbox, msg)

link = tm.wait_for_link(inbox, timeout_secs=180)
# → open / POST `link` as required by the target site
```

Manual poll:

```python
msgs = tm.list_messages(inbox)
if msgs:
    body = tm.read_message(inbox, msgs[0])

# TempInbox also binds list/read after mint:
msgs = inbox.list_messages()
body = inbox.read_message(msgs[0])
```

## One-shot create overrides

```python
tm = TempMail()
inbox = tm.create("guerrillamail")  # this call only
inbox = tm.create(order=["1secmail", "mail.tm"])
```

## TempInbox fields agents actually use

| Field / method | Meaning |
| --- | --- |
| `inbox.email` / `inbox.address` | Generated address |
| `inbox.provider` | Which provider minted it |
| `inbox.token` | Session / JWT / opaque auth |
| `inbox.password` | When provider uses one (e.g. mail.tm) |
| `inbox.credentials` | Dict: email + provider + token + session keys |
| `inbox.meta` | All provider-specific extras |
| `inbox.to_dict()` | Full serializable snapshot |
| `inbox.list_messages()` | List messages (if bound) |
| `inbox.read_message(msg)` | Read body (if bound) |

## Router surface (`TempMail`)

```python
tm = TempMail("mail.tm")                 # sticky
tm = TempMail()                          # fallback + DEFAULT_ORDER
tm = TempMail(mode="fallback", order=[…])

tm.mode / tm.provider / tm.order
tm.providers()                           # registered names
tm.set_order([...])
tm.set_mode("sticky", provider="mail.tm")
tm.set_mode("fallback", provider="tempmail.net")

tm.create() / tm.create("guerrillamail") / tm.create(order=[…])
tm.list_messages(inbox)
tm.read_message(inbox, msg)
tm.get_message(inbox, message_id)        # if provider supports
tm.delete_message(inbox, message_id)     # if provider supports
tm.destroy(inbox)                        # if provider supports
tm.wait_for_message(inbox, timeout_secs=120)
tm.wait_for_link(inbox, timeout_secs=180)

tm.generate("mail.tm")                   # raw IProviderGenerateService
tm.inbox_service("mail.tm")              # raw IProviderInboxService
```

Default fallback order:
`{order}`

## Keyed providers

```python
import os
from inboxkit import TempMail

tm = TempMail("smailpro", api_key=os.environ["SMAILPRO_API_KEY"])
tm = TempMail("temp-mail.org", api_key=os.environ["TEMP_MAIL_API_KEY"])
# or set env and omit api_key=
```

| Env var | Provider |
| --- | --- |
| `SMAILPRO_API_KEY` | `smailpro` |
| `TEMP_MAIL_API_KEY` / `TEMPMAIL_IO_API_KEY` | `temp-mail.org` / `temp-mail.io` |

## Raw SDK (bypass router)

```python
from inboxkit import ProviderFactory

factory = ProviderFactory.default()
gen = factory.create_generate("mail.tm")
inbox = gen.mint()
ib = factory.create_inbox("mail.tm")
msgs = ib.list_messages(inbox)
```

## Thin helpers

```python
from inboxkit import create_inbox, list_providers, poll_verify_link

inbox = create_inbox("mail.tm")
link = poll_verify_link(inbox, timeout_secs=180)
print(list_providers())
```

## Errors agents should catch

| Error | When |
| --- | --- |
| `UnknownProviderError` | Bad provider name |
| `AllProvidersFailedError` | Fallback exhausted |
| `VerifyTimeoutError` | `wait_for_*` timed out |
| `BadInputError` | Invalid mode / sticky without provider |
| `UnprocessableError` | Method unsupported on that provider |
| `InboxNotBoundError` | list/read on unbound TempInbox |

```python
from inboxkit import (
    AllProvidersFailedError,
    UnknownProviderError,
    VerifyTimeoutError,
)
```

## Do / don't

**Do**
- Use sticky when the target site needs a stable provider/domain.
- Use fallback when reliability matters more than which domain you get.
- Persist `inbox.to_dict()` / `credentials` if you must re-open the mailbox later.
- Keep timeouts generous (90–180s) for verify links.

**Don't**
- Invent provider API URLs — use the SDK methods only.
- Commit API keys or mailbox tokens.
- Assume every provider supports delete/destroy/get_message.
- Use disposable mail for sensitive accounts.
{provider_block}
## Discoverability

```bash
python -m inboxkit docs          # print this guide
python -m inboxkit providers     # list provider names
python -m inboxkit version       # package version
inboxkit docs                    # same, if scripts installed
```

```python
from inboxkit import docs, __version__
print(docs())
```
""".strip() + "\n"


def print_docs(file: TextIO | None = None, *, include_providers: bool = True) -> None:
    """Write :func:`docs` to ``file`` (default stdout)."""
    import sys

    out = file if file is not None else sys.stdout
    out.write(docs(include_providers=include_providers))
    out.flush()


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``inboxkit`` / ``python -m inboxkit``."""
    import argparse
    import sys

    from inboxkit import __version__
    from inboxkit.router.tempmail import TempMail

    parser = argparse.ArgumentParser(
        prog="inboxkit",
        description="inboxkit — disposable email toolkit (agent-friendly docs).",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"inboxkit {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    p_docs = sub.add_parser(
        "docs",
        help="Print the agent handover usage guide (default command).",
    )
    p_docs.add_argument(
        "--no-providers",
        action="store_true",
        help="Omit the provider bullet list.",
    )

    sub.add_parser("providers", help="List registered provider names.")
    sub.add_parser("version", help="Print package version.")

    args = parser.parse_args(argv)

    # Default to docs when no subcommand — agents often run bare `python -m inboxkit`
    command = args.command or "docs"

    if command == "docs":
        print_docs(include_providers=not getattr(args, "no_providers", False))
        return 0
    if command == "providers":
        for name in TempMail.DEFAULT_ORDER:
            sys.stdout.write(f"{name}\n")
        return 0
    if command == "version":
        sys.stdout.write(f"{__version__}\n")
        return 0

    parser.print_help()
    return 2


__all__ = ["docs", "main", "print_docs"]
