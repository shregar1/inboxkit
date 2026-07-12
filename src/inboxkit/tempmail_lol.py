"""Back-compat shim → tempmail.services.providers.tempmail_lol."""
from inboxkit.services.providers.tempmail_lol import *  # noqa: F401,F403
from inboxkit.services.providers.tempmail_lol import mint, list_messages, read_message, _list, _read  # noqa: F401
