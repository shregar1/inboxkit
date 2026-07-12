"""Providers are first-class packages under services.providers (no root shims)."""

from __future__ import annotations

import importlib


def test_provider_packages_export_mint_and_list_read():
    names = [
        "guerrillamail",
        "maildrop",
        "mailtm",
        "secmail",
        "smailpro",
        "temp_mail_app",
        "temp_mail_org",
        "tempail",
        "tempmail_lol",
        "tempmail_net",
        "tempy",
    ]
    for name in names:
        mod = importlib.import_module(f"inboxkit.services.providers.{name}")
        assert callable(getattr(mod, "mint"))
        assert callable(getattr(mod, "list_messages"))
        assert callable(getattr(mod, "read_message"))
