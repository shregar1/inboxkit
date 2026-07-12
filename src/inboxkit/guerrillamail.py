"""Back-compat shim → tempmail.services.providers.guerrillamail."""
from inboxkit.services.providers.guerrillamail import *  # noqa: F401,F403
from inboxkit.services.providers.guerrillamail import mint, list_messages, read_message, _list, _read  # noqa: F401
