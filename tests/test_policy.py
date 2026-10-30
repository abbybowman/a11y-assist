"""Allowlist decisions for top-level navigation URLs."""

from __future__ import annotations

import pytest

from a11y_assist.policy import check_url

DEFAULT = [".gov", ".mil"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.nasa.gov/",
        "https://nasa.gov",
        "http://section508.gov/path?q=1",
        "https://www.army.mil/",
        "https://WWW.NASA.GOV./",
        "about:blank",
    ],
)
def test_allowed(url: str) -> None:
    assert check_url(url, DEFAULT, dev_mode=False).allowed


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/",
        "https://nasa.gov.evil.com/",
        "https://evilgov/",
        "https://notgov.com/x.gov",
        "https://x.gov@evil.com/",
        "https://user:pw@nasa.gov/",
        "javascript:alert(1)",
        "data:text/html,hi",
        "ftp://nasa.gov/",
        "file:///C:/fixtures/page.html",
        "https:///nohost",
    ],
)
def test_blocked(url: str) -> None:
    assert not check_url(url, DEFAULT, dev_mode=False).allowed


def test_file_allowed_only_in_dev_mode() -> None:
    url = "file:///C:/fixtures/page.html"
    assert not check_url(url, DEFAULT, dev_mode=False).allowed
    assert check_url(url, DEFAULT, dev_mode=True).allowed


def test_dev_mode_does_not_widen_hosts() -> None:
    assert not check_url("https://example.com/", DEFAULT, dev_mode=True).allowed


def test_exact_host_entry() -> None:
    assert check_url("http://127.0.0.1:8000/", ["127.0.0.1"], False).allowed
    assert not check_url("http://127.0.0.2/", ["127.0.0.1"], False).allowed
