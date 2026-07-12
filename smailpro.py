"""Back-compat shim → tempmail.services.providers.smailpro."""
from inboxkit.services.providers.smailpro import *  # noqa: F401,F403
from inboxkit.services.providers.smailpro import mint, list_messages, read_message, _list, _read  # noqa: F401
