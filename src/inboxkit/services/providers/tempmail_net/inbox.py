from __future__ import annotations

from inboxkit.errors.provider.tempmail_net import TempmailNetError
from inboxkit.services.providers.tempail.inbox import TempailInboxService


class TempmailNetInboxService(TempailInboxService):
    """tempmail.net inbox — kontrol/oku/sil/duzelt on https://tempmail.net/."""

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
