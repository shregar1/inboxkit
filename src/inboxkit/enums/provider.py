from __future__ import annotations

from typing import Any

from inboxkit.abstractions import IEnum


class Provider(str, IEnum):
    """Supported disposable-inbox providers."""

    TEMP_MAIL_ORG = "temp-mail.org"
    TEMPAIL = "tempail"
    TEMPMAIL_NET = "tempmail.net"
    GUERRILLAMAIL = "guerrillamail"
    MAIL_TM = "mail.tm"
    MAILDROP = "maildrop"
    TEMPY_EMAIL = "tempy.email"
    TEMPMAIL_LOL = "tempmail.lol"
    TEMP_MAIL_APP = "temp-mail.app"
    ONE_SECMAIL = "1secmail"
    SMAILPRO = "smailpro"

    @classmethod
    def coerce(cls, value: str | Provider | None) -> Provider | None:
        if value is None:
            return None
        if isinstance(value, Provider):
            return value
        key = value.strip().lower()
        for member in cls:
            if member.value == key or member.name.lower() == key.replace(".", "_").replace("-", "_"):
                return member
        aliases = {
            "temp-mail.io": cls.TEMP_MAIL_ORG,
            "tempmail.io": cls.TEMP_MAIL_ORG,
            "tempmailio": cls.TEMP_MAIL_ORG,
            "tempmail.org": cls.TEMP_MAIL_ORG,
            "tempmailorg": cls.TEMP_MAIL_ORG,
            "tempail.com": cls.TEMPAIL,
            "tempmailnet": cls.TEMPMAIL_NET,
            "mailtm": cls.MAIL_TM,
            "guerrilla": cls.GUERRILLAMAIL,
            "secmail": cls.ONE_SECMAIL,
            "tempy": cls.TEMPY_EMAIL,
            "tempmail-lol": cls.TEMPMAIL_LOL,
            "tempmailapp": cls.TEMP_MAIL_APP,
            "smailpro.com": cls.SMAILPRO,
            "sonjj": cls.SMAILPRO,
            "temp-gmail": cls.SMAILPRO,
        }
        return aliases.get(key)
