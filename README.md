# inboxkit

**One API. Eleven disposable-mail providers. Sticky or fallback.**

`inboxkit` is a Python package for minting temporary inboxes, reading messages, and pulling verification links — without wiring each provider by hand. Point it at a provider, or let it fall through an ordered list until one works.

> **Use at your own will and risk.** This is a free tool with no copyright
> claim restricting use, **no warranty**, and **no liability**. Temporary-mail
> providers are independent third parties. You alone are responsible for how
> you use disposable addresses, for obeying provider terms and the law, and
> for never putting sensitive mail in a throwaway inbox. Full text:
> [LICENSE](./LICENSE).

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
python -c "from inboxkit import InboxKit, __version__; print(__version__, InboxKit.DEFAULT_ORDER[:3])"
```

> Optional paid providers need env keys — see [Environment](#environment).

---

## For AI agents

New to this package? Load the built-in handover guide (recipes, API surface, pitfalls):

```bash
python -m inboxkit docs
# or, after install:
inboxkit docs
```

```python
from inboxkit import docs
print(docs())          # full markdown guide as a string
```

Also: `python -m inboxkit providers` · `python -m inboxkit version`

---

## Usage

### 1. Sticky — pin one provider

```python
from inboxkit import InboxKit

tm = InboxKit("mail.tm")          # only this provider; no fallback
inbox = tm.create()

print(inbox.email)                # e.g. jane.doe42@mail.tm
print(inbox.provider)             # mail.tm
print(inbox.credentials)          # token / password / session bundle
print(inbox.to_dict())            # full serializable snapshot
```

### 2. Fallback — try until one works

```python
from inboxkit import InboxKit, RouterMode

# uses InboxKit.DEFAULT_ORDER internally
tm = InboxKit()
inbox = tm.create()
print(inbox.email, "via", inbox.provider)

# or your own order
tm = InboxKit(
    mode=RouterMode.FALLBACK,
    order=["tempmail.net", "mail.tm", "1secmail", "guerrillamail"],
)
inbox = tm.create()

# change order later
tm.set_order(["maildrop", "tempy.email"])
inbox = tm.create()
```

### 3. Read mail and grab a verify link

Typical signup flow: mint → submit the address somewhere → wait for the message.

```python
from inboxkit import InboxKit

tm = InboxKit("mail.tm")
inbox = tm.create()
print("use this address:", inbox.email)

# … register / request reset with inbox.email …

# block until a message arrives
msg = tm.wait_for_message(inbox, timeout_secs=120)
print(msg)  # provider-shaped dict (subject, id, …)

body = tm.read_message(inbox, msg)
print(body)

# or jump straight to the first http(s) link in any new mail
link = tm.wait_for_link(inbox, timeout_secs=180)
print("verify:", link)
```

You can also poll yourself:

```python
msgs = tm.list_messages(inbox)
if msgs:
    body = tm.read_message(inbox, msgs[0])
```

`TempInbox` also binds list/read when minted:

```python
msgs = inbox.list_messages()
body = inbox.read_message(msgs[0])
```

### 4. One-shot overrides on `create()`

```python
tm = InboxKit()  # fallback

# mint from a specific provider this call only
inbox = tm.create("guerrillamail")

# mint with a one-shot fallback order
inbox = tm.create(order=["1secmail", "mail.tm", "tempmail.lol"])
```

### 5. Credentials you may need later

```python
inbox = InboxKit("mail.tm").create()

inbox.email
inbox.address
inbox.token
inbox.password        # when the provider uses one (e.g. mail.tm)
inbox.local
inbox.domain
inbox.display_name
inbox.view_url
inbox.credentials     # auth bundle for re-access
inbox.meta            # every provider-specific field
inbox.to_dict()
```

Example `credentials` shape (fields vary by provider):

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

### 6. Switch mode at runtime

```python
tm = InboxKit()  # started in fallback

tm.set_mode("sticky", provider="mail.tm")
tm.set_mode("fallback", provider="tempmail.net")  # prefer first in order
tm.set_order(["mail.tm", "1secmail"])
print(tm.mode, tm.provider, tm.order)
print(tm.providers())  # all registered names
```

### 7. Delete / destroy (when the provider supports it)

```python
tm = InboxKit("mail.tm")
inbox = tm.create()
msgs = tm.list_messages(inbox)

if msgs:
    tm.delete_message(inbox, msgs[0].get("id") or msgs[0])

tm.destroy(inbox)  # forget mailbox / account when supported
```

### 8. Paid / keyed providers

```python
import os
from inboxkit import InboxKit

# via env: SMAILPRO_API_KEY / TEMP_MAIL_API_KEY
tm = InboxKit("smailpro")
tm = InboxKit("temp-mail.org")

# or pass explicitly
tm = InboxKit("smailpro", api_key=os.environ["SMAILPRO_API_KEY"])
tm = InboxKit("temp-mail.org", api_key=os.environ["TEMP_MAIL_API_KEY"])
inbox = tm.create()
```

### 9. Raw provider SDK (bypass the router)

```python
from inboxkit import ProviderFactory

factory = ProviderFactory.default()

gen = factory.create_generate("mail.tm")
inbox = gen.mint()

ib = factory.create_inbox("mail.tm")
msgs = ib.list_messages(inbox)
body = ib.read_message(inbox, msgs[0]) if msgs else ""
```

### 10. Thin helpers

```python
from inboxkit import create_inbox, list_providers, poll_verify_link

print(list_providers())
inbox = create_inbox("mail.tm")
link = poll_verify_link(inbox, timeout_secs=180)
```

Prefer `InboxKit` for new code.

---

## Why

| Problem | What this package does |
| --- | --- |
| Every temp-mail site has a different API | One `InboxKit` router |
| Providers go down / rate-limit | **Fallback mode** walks an order until mint succeeds |
| You need the email *and* how to read it | `TempInbox` returns address + credentials + meta |
| You still want raw SDKs | Per-provider generate/inbox services via `ProviderFactory` |

Built with SOLID layering: abstractions → factories → router → provider SDKs.

---

## Router API (cheat sheet)

```python
tm = InboxKit("mail.tm")                 # sticky
tm = InboxKit()                          # fallback + DEFAULT_ORDER
tm = InboxKit(mode="fallback", order=[…])

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

Default fallback order (`InboxKit.DEFAULT_ORDER`):

| # | Provider | Notes |
| --- | --- | --- |
| 1 | `temp-mail.org` | Also `temp-mail.io` — official API if `TEMP_MAIL_API_KEY` |
| 2 | `tempail` | Session / cookie API (`tempail.com`) |
| 3 | `tempmail.net` | Same oturum stack as tempail |
| 4 | `guerrillamail` | Public GuerrillaMail AJAX API |
| 5 | `mail.tm` | Account + JWT (`api.mail.tm`) |
| 6 | `maildrop` | GraphQL mailbox |
| 7 | `tempy.email` | Tempy API |
| 8 | `tempmail.lol` | InboxKit.lol |
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
tm = InboxKit("smailpro", api_key="…")          # or rely on env
tm = InboxKit("temp-mail.org", api_key="…")
```

---

## Architecture

```
src/inboxkit/
  abstractions/     I* contracts (IService, IFactory, IError, …)
  models/           TempInbox
  enums/            Provider, RouterMode
  errors/           typed errors + per-provider errors
  utilities/        HttpUtility, NameUtility, PasswordUtility, VerifyUtility
  factories/        ProviderFactory — builds generate/inbox services
  router/           InboxKit — public sticky / fallback facade
  services/         InboxService + providers/*/generate|inbox
tests/              contract + surface + router tests
```

```text
You ──► InboxKit (router)
            │
            ├─ sticky ──► ProviderFactory.create_generate(name).mint()
            │
            └─ fallback ► try order[0], order[1], … until success
                              │
                              └─ TempInbox { email, token, meta, credentials }
```

DIP: inject a custom `ProviderFactory` or `order` in tests — no globals required.

```python
from inboxkit import InboxKit, ProviderFactory

factory = ProviderFactory.default()
tm = InboxKit(mode="fallback", factory=factory, order=["mail.tm", "1secmail"])
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Coverage is gated at **95%** (`fail_under` in `pyproject.toml`).

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
