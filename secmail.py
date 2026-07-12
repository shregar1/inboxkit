"""Back-compat shim → tempmail.services.providers.secmail."""
from inboxkit.services.providers.secmail import *  # noqa: F401,F403
from inboxkit.services.providers.secmail import mint, list_messages, read_message, _list, _read  # noqa: F401
