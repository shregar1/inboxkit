"""Back-compat shim → tempmail.services.providers.tempy."""
from inboxkit.services.providers.tempy import *  # noqa: F401,F403
from inboxkit.services.providers.tempy import mint, list_messages, read_message, _list, _read  # noqa: F401
