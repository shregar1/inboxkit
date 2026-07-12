"""Back-compat shim → tempmail.services.providers.tempail."""
from inboxkit.services.providers.tempail import *  # noqa: F401,F403
from inboxkit.services.providers.tempail import mint, list_messages, read_message, _list, _read  # noqa: F401
