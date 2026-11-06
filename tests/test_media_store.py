"""The media store (capture.py; 2.A-2.D plan items 13-14, Q9): media saved
in full while recording, inside the HAR zip, and its byte ranges answered on
replay. Pages and media come from the local test server (no network)."""

from __future__ import annotations

from tobi508.capture import media_body, media_index, record, replay_context

from .conftest import noop_log

RANGE_JS = """async (url) => {
  const r = await fetch(url, { headers: { Range: 'bytes=10-109' } });
  const b = await r.arrayBuffer();
  const range = r.headers.get('content-range');
  return { status: r.status, length: b.byteLength, range };
}"""


async def test_media_is_stored_and_ranges_replay(settings, browser, server, tmp_path):
    har = tmp_path / "page.har.zip"
    cap = await record(
        browser, settings, f"{server.base}/2x/t-autoplay.html", har, noop_log
    )
    [m] = cap.media
    assert m["url"].endswith("/tone.wav") and m["file"] and m["size"] > 60_000
    assert media_index(har)[0]["file"] == m["file"]
    body = media_body(har, m["url"])
    assert body is not None and len(body) == m["size"]
    r = await replay_context(browser, settings, har, noop_log)
    try:
        page = await r.context.new_page()
        await r.guard.goto(page, cap.final_url)
        got = await page.evaluate(RANGE_JS, m["url"])
    finally:
        await r.context.close()
    assert got == {
        "status": 206,
        "length": 100,
        "range": f"bytes 10-109/{m['size']}",
    }, got


async def test_media_over_the_cap_is_marked(settings, browser, server, tmp_path):
    small = settings.model_copy(update={"media_cap_mb": 0.01})  # 10 kB
    har = tmp_path / "page.har.zip"
    cap = await record(
        browser, small, f"{server.base}/2x/t-autoplay.html", har, noop_log
    )
    [m] = cap.media
    assert m["over_cap"] and m["file"] is None and m["size"] > 10_000
