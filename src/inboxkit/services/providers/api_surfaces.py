"""Public API surfaces researched per provider (sources linked in abstractions).

Only endpoints that exist on each provider are implemented — no fake delete/update.
"""

from __future__ import annotations

# Summary table for humans; contracts live on I*GenerateService / I*InboxService.

API_SURFACES: dict[str, dict[str, object]] = {
    "mail.tm": {
        "docs": "https://docs.mail.tm/",
        "base": "https://api.mail.tm",
        "generate": [
            "list_domains",
            "get_domain",
            "create_account",
            "get_token",
            "get_account",
            "delete_account",
            "me",
            "mint",
        ],
        "inbox": [
            "list_messages",
            "get_message",
            "read_message",
            "delete_message",
            "mark_seen",
            "get_source",
        ],
    },
    "guerrillamail": {
        "docs": "https://www.guerrillamail.com/GuerrillaMailAPI.html",
        "base": "https://api.guerrillamail.com/ajax.php",
        "generate": [
            "get_email_address",
            "set_email_user",
            "forget_me",
            "extend",
            "mint",
        ],
        "inbox": [
            "check_email",
            "get_email_list",
            "list_messages",
            "fetch_email",
            "read_message",
            "delete_messages",
        ],
    },
    "maildrop": {
        "docs": "https://docs.maildrop.cc/",
        "base": "https://api.maildrop.cc/graphql",
        "generate": ["ping", "statistics", "status", "altinbox", "mint"],
        "inbox": ["list_messages", "get_message", "read_message", "delete_message"],
    },
    "1secmail": {
        "docs": "https://www.1secmail.com/api/v1/",
        "base": "https://www.1secmail.com/api/v1/",
        "generate": ["list_domains", "gen_random_mailbox", "mint"],
        "inbox": ["list_messages", "get_message", "read_message", "download_attachment"],
        "notes": "No public delete/update",
    },
    "tempy.email": {
        "docs": "https://tempy.email/developers",
        "base": "https://tempy.email/api/v1",
        "generate": ["create_mailbox", "get_mailbox", "delete_mailbox", "mint"],
        "inbox": ["list_messages", "read_message"],
    },
    "tempmail.lol": {
        "docs": "https://github.com/tempmail-lol/tempmail-api-javascript",
        "base": "https://api.tempmail.lol",
        "generate": ["create_inbox", "set_webhook", "remove_webhook", "mint"],
        "inbox": ["check_inbox", "list_messages", "read_message"],
        "notes": "No per-message delete; inbox TTL expiry",
    },
    "temp-mail.org": {
        "docs": "https://docs.temp-mail.io/docs/getting-started",
        "site": "https://temp-mail.io/en",
        "aliases": ["temp-mail.io", "tempmail.io", "tempmailio", "tempmail.org"],
        "base_web": "https://api.internal.temp-mail.io/api/v3",
        "base_official": "https://api.temp-mail.io/v1",
        "generate": [
            "list_domains",
            "create_email",
            "delete_email",
            "rate_limit",
            "mint",
        ],
        "inbox": [
            "list_messages",
            "get_message",
            "read_message",
            "delete_message",
            "get_source",
            "download_attachment",
        ],
        "notes": "Same product as temp-mail.io; TEMP_MAIL_API_KEY → official; else free web",
    },
    "tempail": {
        "docs": None,
        "site": "https://tempail.com/en/",
        "aliases": ["tempail.com"],
        "base": "https://tempail.com",
        "generate": [
            "fetch_session",
            "destroy_mailbox",
            "recover_qr",
            "mint",
        ],
        "inbox": [
            "poll_inbox",
            "list_messages",
            "get_message",
            "read_message",
            "delete_message",
            "mark_message",
        ],
        "notes": "Unofficial session API; may hit reCAPTCHA (bot-kontrol.php)",
    },
    "tempmail.net": {
        "docs": None,
        "site": "https://tempmail.net/",
        "aliases": ["tempmailnet"],
        "base": "https://tempmail.net",
        "generate": [
            "fetch_session",
            "destroy_mailbox",
            "mint",
        ],
        "inbox": [
            "poll_inbox",
            "list_messages",
            "get_message",
            "read_message",
            "delete_message",
            "mark_message",
        ],
        "notes": "Same oturum stack as tempail; 304 on kontrol = no change; no sifre/QR",
    },
    "temp-mail.app": {
        "docs": None,
        "base": "https://temp-mail.app",
        "generate": ["create_address", "mint"],
        "inbox": ["list_messages", "read_message"],
        "notes": "Undocumented site API; no public delete/update",
    },
    "smailpro": {
        "docs": "https://sonjj.com/docs/",
        "base": "https://app.sonjj.com",
        "generate": [
            "list_domains",
            "create_email",
            "random_gmail",
            "list_gmail",
            "random_outlook",
            "list_outlook",
            "mint",
        ],
        "inbox": [
            "list_messages",
            "get_message",
            "read_message",
            "remove_gmail_message",
            "list_attachments",
        ],
        "notes": "Requires SMAILPRO_API_KEY; see https://smailpro.com/api",
    },
}
