"""Multi-provider disposable inbox toolkit.

Layout:
  abstractions/  I* interfaces
  models/        TempInbox handle
  constants/     shared constants
  enums/         IEnum / Provider
  errors/        IError + concrete errors
  utilities/     IUtility helpers
  factories/     IFactory / ProviderFactory
  router/        InboxKit public router (use this)
  services/      IService orchestration + providers/

Usage:
  from inboxkit import InboxKit, RouterMode

  # sticky — pinned provider, no fallback
  tm = InboxKit("mail.tm")
  inbox = tm.create()

  # fallback — internal DEFAULT_ORDER
  tm = InboxKit()
  inbox = tm.create()

  # fallback — custom order
  tm = InboxKit(mode=RouterMode.FALLBACK, order=["tempmail.net", "mail.tm"])
  tm.set_order(["guerrillamail", "1secmail"])

Agent handover (full usage guide):
  python -m inboxkit docs
  from inboxkit import docs; print(docs())
"""

from __future__ import annotations

__version__ = "0.1.0"

from inboxkit.abstractions import (
    IAbstraction,
    IConstant,
    IEnum,
    IError,
    IFactory,
    IService,
    IUtility,
)
from inboxkit.models import TempInbox
from inboxkit.constants import PROVIDER_ORDER
from inboxkit.enums import Provider, RouterMode
from inboxkit.errors import (
    AllProvidersFailedError,
    BadInputError,
    ConflictError,
    ForbiddenError,
    GuerrillaMailError,
    InboxNotBoundError,
    InternalError,
    IProviderError,
    MailDropError,
    MailTmError,
    NotFoundError,
    ProviderError,
    RateLimitError,
    SecMailError,
    SmailProError,
    TempMailAppError,
    TempMailError,
    TempMailLolError,
    TempMailOrgError,
    TempyError,
    TempailError,
    TempmailNetError,
    TimeoutError,
    UnauthorizedError,
    UnavailableError,
    UnknownProviderError,
    UnprocessableError,
    VerifyTimeoutError,
)
from inboxkit.factories import (
    IProviderFactory,
    ProviderFactory,
    ProviderRegistration,
)
from inboxkit.router import IInboxKitRouter, InboxKit

from inboxkit.services import (
    InboxService,
    IProviderGenerateService,
    IProviderInboxService,
    IProviderService,
    create_inbox,
    list_providers,
    poll_verify_link,
)
from inboxkit.services.providers import (
    guerrillamail,
    maildrop,
    mailtm,
    secmail,
    smailpro,
    temp_mail_app,
    temp_mail_org,
    tempail,
    tempmail_net,
    tempmail_lol,
    tempy,
)
from inboxkit.services.providers.spec import ProviderSpec
from inboxkit.utilities import (
    HttpUtility,
    NameUtility,
    PasswordUtility,
    VerifyUtility,
)
from inboxkit.docs import docs, print_docs

__all__ = [
    "AllProvidersFailedError",
    "BadInputError",
    "ConflictError",
    "ForbiddenError",
    "GuerrillaMailError",
    "HttpUtility",
    "IAbstraction",
    "IConstant",
    "IEnum",
    "IError",
    "IFactory",
    "IProviderError",
    "IProviderFactory",
    "IProviderGenerateService",
    "IProviderInboxService",
    "IProviderService",
    "IService",
    "IInboxKitRouter",
    "IUtility",
    "InboxNotBoundError",
    "InboxService",
    "InternalError",
    "MailDropError",
    "MailTmError",
    "NameUtility",
    "NotFoundError",
    "PROVIDER_ORDER",
    "PasswordUtility",
    "Provider",
    "ProviderError",
    "ProviderFactory",
    "ProviderRegistration",
    "ProviderSpec",
    "RateLimitError",
    "RouterMode",
    "SecMailError",
    "SmailProError",
    "TempInbox",
    "InboxKit",
    "TempMailAppError",
    "TempMailError",
    "TempMailLolError",
    "TempMailOrgError",
    "TempailError",
    "TempmailNetError",
    "TempyError",
    "TimeoutError",
    "UnauthorizedError",
    "UnavailableError",
    "UnknownProviderError",
    "UnprocessableError",
    "VerifyTimeoutError",
    "VerifyUtility",
    "__version__",
    "create_inbox",
    "docs",
    "guerrillamail",
    "list_providers",
    "maildrop",
    "mailtm",
    "poll_verify_link",
    "print_docs",
    "secmail",
    "smailpro",
    "temp_mail_app",
    "temp_mail_org",
    "tempail",
    "tempmail_net",
    "tempmail_lol",
    "tempy",
]
