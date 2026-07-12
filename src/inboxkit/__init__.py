"""Multi-provider disposable inbox toolkit.

Layout:
  abstractions/  I* interfaces
  models/        TempInbox handle
  constants/     shared constants
  enums/         IEnum / Provider
  errors/        IError + concrete errors
  utilities/     IUtility helpers
  factories/     IFactory / ProviderFactory
  router/        TempMail public router (use this)
  services/      IService orchestration + providers/

Usage:
  from inboxkit import TempMail, RouterMode

  # sticky — pinned provider, no fallback
  tm = TempMail("mail.tm")
  inbox = tm.create()

  # fallback — internal DEFAULT_ORDER
  tm = TempMail()
  inbox = tm.create()

  # fallback — custom order
  tm = TempMail(mode=RouterMode.FALLBACK, order=["tempmail.net", "mail.tm"])
  tm.set_order(["guerrillamail", "1secmail"])
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
from inboxkit.router import ITempMailRouter, TempMail
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
    "ITempMailRouter",
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
    "TempMail",
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
    "guerrillamail",
    "list_providers",
    "maildrop",
    "mailtm",
    "poll_verify_link",
    "secmail",
    "smailpro",
    "temp_mail_app",
    "temp_mail_org",
    "tempail",
    "tempmail_net",
    "tempmail_lol",
    "tempy",
]
