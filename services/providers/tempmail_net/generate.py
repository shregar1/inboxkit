from __future__ import annotations

from inboxkit.errors.provider.tempmail_net import TempmailNetError
from inboxkit.services.providers.tempail.generate import TempailGenerateService
from inboxkit.services.providers.tempmail_net.inbox import TempmailNetInboxService


class TempmailNetGenerateService(TempailGenerateService):
    """tempmail.net mint — same oturum flow as tempail, different host.

    Site: https://tempmail.net/
    """

    SITE = "https://tempmail.net"
    HOME = "https://tempmail.net/"
    PROVIDER = "tempmail.net"
    DEFAULT_APIS = {
        "kontrol": "https://tempmail.net/en/api/kontrol/",
        "oku": "https://tempmail.net/en/api/oku/",
        "sil": "https://tempmail.net/en/api/sil/",
        "duzelt": "https://tempmail.net/en/api/duzelt/",
        "yoket": "https://tempmail.net/en/api/yoket/",
        "iletisim": "https://tempmail.net/en/api/iletisim/",
    }
    _error_cls = TempmailNetError
    _inbox_cls = TempmailNetInboxService
