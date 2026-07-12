"""Back-compat shim → tempmail.services.providers.mailtm."""
from inboxkit.services.providers.mailtm import *  # noqa: F401,F403
from inboxkit.services.providers.mailtm import mint, list_messages, read_message, _list, _read  # noqa: F401
