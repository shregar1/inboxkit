"""Tests for agent docs CLI / API."""

from __future__ import annotations

import io

import pytest

from inboxkit import __version__, docs, print_docs
from inboxkit.docs import main


def test_docs_returns_agent_guide():
    text = docs()
    assert "inboxkit agent handover guide" in text
    assert __version__ in text
    assert "from inboxkit import InboxKit" in text
    assert "wait_for_link" in text
    assert "mail.tm" in text


def test_docs_can_omit_providers():
    full = docs(include_providers=True)
    slim = docs(include_providers=False)
    assert "## Providers (default fallback order)" in full
    assert "## Providers (default fallback order)" not in slim


def test_print_docs_writes_stdout():
    buf = io.StringIO()
    print_docs(buf)
    assert "InboxKit" in buf.getvalue()


def test_cli_docs_default(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "agent handover guide" in out


def test_cli_docs_no_providers(capsys):
    assert main(["docs", "--no-providers"]) == 0
    out = capsys.readouterr().out
    assert "agent handover guide" in out
    assert "## Providers (default fallback order)" not in out


def test_cli_providers(capsys):
    assert main(["providers"]) == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert "mail.tm" in lines
    assert "1secmail" in lines


def test_cli_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_cli_unknown_falls_through_to_help(capsys):
    # argparse rejects unknown subcommands before main's fallback
    with pytest.raises(SystemExit) as ei:
        main(["nope"])
    assert ei.value.code == 2


def test_module_main_entrypoint(monkeypatch):
    import runpy
    import sys

    monkeypatch.setattr(sys, "argv", ["inboxkit", "version"])
    with pytest.raises(SystemExit) as ei:
        runpy.run_module("inboxkit", run_name="__main__")
    assert ei.value.code == 0
