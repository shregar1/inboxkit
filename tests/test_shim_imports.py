"""Import root back-compat shim modules (and base re-exports)."""

from __future__ import annotations


def test_import_all_root_shims():
    import inboxkit.base as base
    import inboxkit.guerrillamail as guerrillamail
    import inboxkit.maildrop as maildrop
    import inboxkit.mailtm as mailtm
    import inboxkit.secmail as secmail
    import inboxkit.smailpro as smailpro
    import inboxkit.temp_mail_app as temp_mail_app
    import inboxkit.temp_mail_org as temp_mail_org
    import inboxkit.tempail as tempail
    import inboxkit.tempmail_lol as tempmail_lol
    import inboxkit.tempmail_net as tempmail_net
    import inboxkit.tempy as tempy

    assert base.UA
    assert hasattr(guerrillamail, "mint")
    assert hasattr(maildrop, "mint")
    assert hasattr(mailtm, "mint")
    assert hasattr(secmail, "mint")
    assert hasattr(smailpro, "mint")
    assert hasattr(temp_mail_app, "mint")
    assert hasattr(temp_mail_org, "mint")
    assert hasattr(tempail, "mint")
    assert hasattr(tempmail_lol, "mint")
    assert hasattr(tempmail_net, "mint")
    assert hasattr(tempy, "mint")
