"""Back-compat shim → tempmail.services.providers.temp_mail_org."""
from inboxkit.services.providers.temp_mail_org import *  # noqa: F401,F403
from inboxkit.services.providers.temp_mail_org import mint, list_messages, read_message, _list, _read  # noqa: F401
