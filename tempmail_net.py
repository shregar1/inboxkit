"""Back-compat shim → tempmail.services.providers.tempmail_net."""
from inboxkit.services.providers.tempmail_net import *  # noqa: F401,F403
from inboxkit.services.providers.tempmail_net import mint, list_messages, read_message, _list, _read  # noqa: F401
