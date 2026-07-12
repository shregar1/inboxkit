# inboxkit

**One API. Eleven disposable-mail providers. Sticky or fallback.**

`inboxkit` is a Python package for minting temporary inboxes, reading messages, and pulling verification links — without wiring each provider by hand. Point it at a provider, or let it fall through an ordered list until one works.

> **Use at your own will and risk.** This is a free tool with no copyright
> claim restricting use, **no warranty**, and **no liability**. Temporary-mail
> providers are independent third parties. You alone are responsible for how
> you use disposable addresses, for obeying provider terms and the law, and
> for never putting sensitive mail in a throwaway inbox. Full text:
> [LICENSE](./LICENSE).

```python
from inboxkit import TempMail

tm = TempMail("mail.tm")          # sticky — pinned provider
inbox = tm.create()

print(inbox.email)                # jane.doe42@mail.tm
print(inbox.credentials)          # token / password / session
print(inbox.to_dict())            # full snapshot

msgs = tm.list_messages(inbox)
body = tm.read_message(inbox, msgs[0])
link = tm.wait_for_link(inbox, timeout_secs=120)
```

---

## Why

| Problem | What this package does |
| --- | --- |
| Every temp-mail site has a different API | One `TempMail` router |
| Providers go down / rate-limit | **Fallback mode** walks an order until mint succeeds |
| You need the email *and* how to read it | `TempInbox` returns address + credentials + meta |
| You still want raw SDKs | Per-provider generate/inbox services via `ProviderFactory` |

Built with SOLID layering: abstractions → factories → router → provider SDKs.

---

## Install

Stdlib only — no third-party runtime dependencies.

```bash
pip install git+https://github.com/shregar1/inboxkit.git
```

Editable (local clone):

```bash
git clone https://github.com/shregar1/inboxkit.git
cd inboxkit
pip install -e ".[dev]"
```

```bash
python -c "from inboxkit import TempMail; print(TempMail.DEFAULT_ORDER)"
```

> Optional paid providers need env keys — see [Environment](#environment).

---

## Quick start

### Sticky mode

Pin one provider. No fallback.

```python
from inboxkit import TempMail

tm = TempMail("tempmail.net")
inbox = tm.create()

assert tm.mode.value == "sticky"
assert tm.provider == "tempmail.net"
```

### Fallback mode

Try providers in order until one mints successfully.

```python
from inboxkit import TempMail, RouterMode

# internal DEFAULT_ORDER
tm = TempMail()
inbox = tm.create()

# your order
tm = TempMail(
    mode=RouterMode.FALLBACK,
    order=["tempmail.net", "mail.tm", "1secmail", "guerrillamail"],
)
inbox = tm.create()

# change order later
tm.set_order(["maildrop", "tempy.email"])
```

### What `create()` returns

A `TempInbox` with everything needed to use the mailbox again:

```python
inbox = tm.create()

inbox.email           # generated address
inbox.address         # same
inbox.token           # session / JWT / API material
inbox.password        # when the provider uses one (e.g. mail.tm)
inbox.local           # local-part
inbox.domain          # domain
inbox.display_name    # if minted
inbox.view_url        # web UI hint when available
inbox.credentials     # auth bundle
inbox.meta            # every provider-specific field
inbox.to_dict()       # full serializable snapshot
```

Example credential shape (provider-dependent):

```python
{
  "email": "user@tozya.com",
  "provider": "tempmail.net",
  "token": "…",
  "oturum": "…",
  "cookie": "PHPSESSID=…; oturum=…",
  "tarih": "…"
}
```

---

## Router API

```python
tm = TempMail("mail.tm")                 # sticky
tm = TempMail()                          # fallback + DEFAULT_ORDER
tm = TempMail(mode="fallback", order=[…])

tm.mode                                  # RouterMode.STICKY | FALLBACK
tm.provider                              # pinned name, or None in fallback
tm.order                                 # canonical try-order
tm.providers()                           # all registered names
tm.set_order(["mail.tm", "1secmail"])
tm.set_mode("sticky", provider="mail.tm")
tm.set_mode("fallback", provider="tempmail.net")  # prefer first

inbox = tm.create()
inbox = tm.create("guerrillamail")       # one-shot sticky mint
inbox = tm.create(order=["1secmail", "mail.tm"])  # one-shot fallback order

tm.list_messages(inbox)
tm.read_message(inbox, msg)
tm.get_message(inbox, message_id)        # when supported
tm.delete_message(inbox, message_id)     # when supported
tm.destroy(inbox)                        # when supported
tm.wait_for_message(inbox, timeout_secs=120)
tm.wait_for_link(inbox, timeout_secs=180)

# escape hatches
tm.generate("mail.tm")                   # IProviderGenerateService
tm.inbox_service("mail.tm")              # IProviderInboxService
```

---

## Providers

Default fallback order (`TempMail.DEFAULT_ORDER`):

| # | Provider | Notes |
| --- | --- | --- |
| 1 | `temp-mail.org` | Also `temp-mail.io` — official API if `TEMP_MAIL_API_KEY` |
| 2 | `tempail` | Session / cookie API (`tempail.com`) |
| 3 | `tempmail.net` | Same oturum stack as tempail |
| 4 | `guerrillamail` | Public GuerrillaMail AJAX API |
| 5 | `mail.tm` | Account + JWT (`api.mail.tm`) |
| 6 | `maildrop` | GraphQL mailbox |
| 7 | `tempy.email` | Tempy API |
| 8 | `tempmail.lol` | TempMail.lol |
| 9 | `temp-mail.app` | Site API |
| 10 | `1secmail` | Also `secmail` |
| 11 | `smailpro` | Sonjj API — requires `SMAILPRO_API_KEY` |

Aliases work everywhere (`mailtm` → `mail.tm`, `tempmailio` → `temp-mail.org`, …).

---

## Environment

| Variable | Used by |
| --- | --- |
| `TEMP_MAIL_API_KEY` / `TEMPMAIL_IO_API_KEY` | temp-mail.org / temp-mail.io official API |
| `SMAILPRO_API_KEY` | smailpro / Sonjj |

```python
tm = TempMail("smailpro", api_key="…")          # or rely on env
tm = TempMail("temp-mail.org", api_key="…")
```

---

## Architecture

```
inboxkit/
  abstractions/     I* contracts (IService, IFactory, IError, …)
  models/           TempInbox
  enums/            Provider, RouterMode
  errors/           typed errors + per-provider errors
  utilities/        HttpUtility, NameUtility, PasswordUtility, VerifyUtility
  factories/        ProviderFactory — builds generate/inbox services
  router/           TempMail — public sticky / fallback facade
  services/         InboxService + providers/*/generate|inbox
  tests/            contract + surface + router tests
```

```text
You ──► TempMail (router)
            │
            ├─ sticky ──► ProviderFactory.create_generate(name).mint()
            │
            └─ fallback ► try order[0], order[1], … until success
                              │
                              └─ TempInbox { email, token, meta, credentials }
```

DIP: inject a custom `ProviderFactory` or `order` in tests — no globals required.

```python
from inboxkit import TempMail, ProviderFactory, ProviderRegistration

factory = ProviderFactory([/* custom registrations */])
tm = TempMail(mode="fallback", factory=factory, order=["a", "b"])
```

---

## Lower-level helpers

Still exported for scripts and apps:

```python
from inboxkit import create_inbox, list_providers, poll_verify_link

inbox = create_inbox("mail.tm")
link = poll_verify_link(inbox, timeout_secs=180)
```

Prefer `TempMail` for new code.

---

## Tests

```bash
cd /path/to/Documents
python -m pytest inboxkit/tests/ -q
```

---

## Design notes

- **ISP** — generate vs inbox services are separate contracts.
- **No fake endpoints** — only methods each provider actually exposes.
- **Captcha / bot walls** — some site scrapers (e.g. tempail) may raise a typed captcha error; use another provider or fallback order.
- **Stdlib HTTP** — `urllib` only; no `requests` / `httpx` required.

---

## License & disclaimer

This is a **free tool**. There is **no copyright claim** intended to restrict
use, copy, modification, or distribution.

### Use at your own will and risk

By using this Software you agree that:

1. **You choose to use it** — voluntarily, at your sole discretion and risk.
   If you disagree with [LICENSE](./LICENSE), do not use the Software.

2. **No warranty** — the Software is provided **“AS IS”** and **“AS
   AVAILABLE”**, without warranties of merchantability, fitness, non-
   infringement, uptime, security, privacy, or compatibility with any
   third-party API or site.

3. **No liability** — authors and contributors are not liable for claims,
   damages, lost data, bans, captchas, fraud, account issues, or any other
   consequence arising from use of the Software or of temporary inboxes it
   creates — to the maximum extent permitted by law.

4. **Third-party providers** — mail.tm, temp-mail.org, GuerrillaMail,
   tempail, tempmail.net, smailpro, and every other integrated service are
   independent. They are not affiliated with or guaranteed by this project.
   You must follow **their** terms, privacy policies, rate limits, and
   billing rules. Unofficial / site-scraping endpoints are fragile and may
   violate a provider’s terms; using them is your choice and risk.

5. **No sensitive use** — disposable inboxes may be public, short-lived, or
   readable by others. **Do not** use them for banking, government ID,
   healthcare, primary email, account recovery, passwords, 2FA backups, or
   secrets.

6. **Lawful use only** — do not use this tool for fraud, phishing, spam,
   harassment, unauthorized access, or any illegal purpose. Misuse is
   entirely your responsibility.

7. **Automation risk** — bots may hit captchas, IP bans, or legal notices.
   Proxies, volume, and consequences are on you. The authors have no duty
   to bypass bot protection or keep unofficial APIs working.

8. **Your secrets** — API keys, tokens, cookies, and passwords returned or
   configured by you stay in your environment. Protect them; do not commit
   them to public repos. There is no DPA or privacy guarantee from this
   tool.

9. **No support contract** — updates, fixes, and help are optional. Examples
   in this README are illustrative only.

10. **Indemnity (where enforceable)** — you are responsible for claims
    arising from your use, your violation of this disclaimer, or your
    violation of third-party rights or terms.

The complete, controlling text is in **[LICENSE](./LICENSE)**. Using the
Software constitutes acceptance. If you need a warranty, SLA, or hosted
service, do not use this tool.
