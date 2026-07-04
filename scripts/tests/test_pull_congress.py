"""Network-resilience tests for pull_congress.download_ptr_text.

The House disclosures server intermittently resets connections (WinError 10054)
mid-run. A single transient ConnectionError must NOT abort a 500+ PTR pull:
download_ptr_text retries with backoff, and on persistent failure returns a
sentinel status (0) so the caller logs it in http_failed and continues.

No real network or PDFs: a fake session injects the failures; a no-op sleep
keeps the tests instant.
"""
import sys
import pathlib

import requests

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import pull_congress  # noqa: E402


class _FlakySession:
    """A fake requests.Session: .get raises ConnectionError `fail_times` times,
    then returns `resp` (or keeps failing if fail_times is huge)."""

    def __init__(self, fail_times, resp=None):
        self.fail_times = fail_times
        self.resp = resp
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise requests.exceptions.ConnectionError("forcibly closed (10054)")
        return self.resp


class _Resp:
    def __init__(self, status_code=200, content=b"not-a-real-pdf"):
        self.status_code = status_code
        self.content = content


def test_download_ptr_text_retries_transient_reset_then_succeeds():
    # Two resets, then a 200. Should NOT raise; should return status 200 after 3 calls.
    sess = _FlakySession(fail_times=2, resp=_Resp(status_code=200))
    text, url, status = pull_congress.download_ptr_text(
        2025, "ABC", session=sess, retries=3, backoff=0, sleep=lambda _s: None
    )
    assert status == 200
    assert sess.calls == 3            # 2 failures + 1 success
    assert url.endswith("/2025/ABC.pdf")
    # content isn't a valid PDF -> pdfplumber fails -> text "" (caller would skip), no crash
    assert text == ""


def test_download_ptr_text_returns_sentinel_after_exhausting_retries():
    # Persistent reset: after `retries` attempts, return ("", url, 0) instead of raising.
    sess = _FlakySession(fail_times=99)
    text, url, status = pull_congress.download_ptr_text(
        2025, "XYZ", session=sess, retries=3, backoff=0, sleep=lambda _s: None
    )
    assert (text, status) == ("", 0)   # status 0 = network-failed sentinel
    assert sess.calls == 3             # tried exactly `retries` times, then gave up
    assert url.endswith("/2025/XYZ.pdf")


def test_download_ptr_text_non_200_is_passed_through_without_retry():
    # A clean 404 is not a transient error: return it immediately, one call only.
    sess = _FlakySession(fail_times=0, resp=_Resp(status_code=404))
    text, url, status = pull_congress.download_ptr_text(
        2025, "GONE", session=sess, retries=3, backoff=0, sleep=lambda _s: None
    )
    assert (text, status) == ("", 404)
    assert sess.calls == 1
