"""Back-compat shim → tempmail.services.providers.maildrop."""
from inboxkit.services.providers.maildrop import *  # noqa: F401,F403
from inboxkit.services.providers.maildrop import mint, list_messages, read_message, _list, _read  # noqa: F401
