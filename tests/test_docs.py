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
    assert "from inboxkit import TempMail" in text
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
    assert "TempMail" in buf.getvalue()


def test_cli_docs_default(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "agent handover guide" in out


def test_cli_docs_explicit(capsys):
    assert main(["docs"]) == 0
    assert "wait_for_message" in capsys.readouterr().out


def test_cli_providers(capsys):
    assert main(["providers"]) == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert "mail.tm" in lines
    assert "1secmail" in lines


def test_cli_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__
