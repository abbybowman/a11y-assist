"""4.C fixtures (docs/rules/4c-build-tasks.md): expected outcomes and behavior.

Two kinds of test per fixture:

* Behavior: the page does what its row says (where Tab goes, which key frees
  focus). These record facts and run now.
* Outcome: run_tt_tests gives the row's expected 4.C outcome. Runs for the
  outcomes the implemented rows decide (DNA so far); the expectation lives in
  EXPECTED, never in a page.

F29 and F33 follow the V10 and V9 decisions (both PASS with a note). F35 was
added to cover M4, which F10 cannot: a native modal lets Tab leave the page.
"""

from __future__ import annotations

import re

import pytest

from a11y_assist.models import TestId
from a11y_assist.pipeline import RunRefused, run_tt_tests
from a11y_assist.traverse import dom_inventory

from .conftest import FIXTURES
from .focus import active, deep_active
from .harness_4c import instance_rows, run_4c

FIX = FIXTURES / "4c"

# Fixture -> expected 4.C outcome, the instance rows it should go through (row
# trace, custom fixtures only) and the answers a correct judge gives (J1
# defaults to "no documented key"). Expectations live here, never in a page.
EXPECTED: dict[str, dict] = {
    "f03-clickable-div": {"outcome": "DNA", "rows": []},
    "f04-field-swallows-tab": {"outcome": "FAIL", "rows": ["M11"]},
    "f05-field-swallows-tab-only": {"outcome": "PASS", "rows": ["M2"], "note": "4.F"},
    "f09-key-in-comment-only": {"outcome": "FAIL", "rows": ["M12"]},
    "f10-native-dialog": {"outcome": "PASS", "rows": []},
    "f11-aria-modal-close-button": {"outcome": "PASS", "rows": ["M4"]},
    "f12-aria-modal-div-close": {"outcome": "FAIL", "rows": ["M12"]},
    "f13-cookie-banner": {"outcome": "PASS", "rows": ["M4"]},
    "f14-zip-gate": {
        "outcome": "NEEDS_REVIEW",
        "rows": ["M8"],
        "j2": {"gate": "yes", "fields": [{"locator": "m1", "value": "12345"}]},
    },
    # A gate made of radio buttons: "input or interaction" (p. 21), 1.8.0.
    "f35-radio-gate": {
        "outcome": "NEEDS_REVIEW",
        "rows": ["M8"],
        "j2": {"gate": "yes", "fields": [{"locator": "m1", "value": "English"}]},
    },
    "f15-account-number-gate": {
        "outcome": "NEEDS_REVIEW",
        "rows": ["M8"],
        "j2": {"gate": "yes", "fields": []},
    },
    "f16-textarea-tab-escape": {"outcome": "PASS", "rows": ["M2"]},
    "f17-editor-captures-tab-escape": {"outcome": "FAIL", "rows": ["M11"]},
    "f18-same-origin-iframe-loop": {"outcome": "FAIL", "rows": ["M12"]},
    "f19-cross-origin-iframe-loop": {"outcome": "FAIL", "rows": ["M12"]},
    # The player's volume slider is a form control, so J2 is asked (1.8.0).
    "f20-cross-origin-player-trap": {
        "outcome": "FAIL",
        "rows": ["M12"],
        "j2": {"gate": "no"},
    },
    "f21-cross-origin-player-ok": {"outcome": "PASS", "rows": []},
    "f22-menubar-roving": {"outcome": "PASS", "rows": []},
    "f23-grid-captures-tab": {"outcome": "FAIL", "rows": ["M12"]},
    "f24-open-shadow-loop": {"outcome": "FAIL", "rows": ["M12"]},
    "f25-closed-shadow-loop": {"outcome": "FAIL", "rows": ["M12"]},
    "f26-element-removes-itself": {"outcome": "PASS", "rows": []},
    "f27-focus-drops-to-body-cycles": {"outcome": "FAIL", "rows": ["M12"]},
    "f29-infinite-feed": {
        "outcome": "PASS",
        "rows": [],
        "note": "more content as you scroll",
    },
    "f30-whole-page-wrap": {"outcome": "PASS", "rows": ["M10"], "note": "whole-page"},
    "f31-loop-exit-is-link": {"outcome": "FAIL", "rows": ["M12"]},
    "f32-two-traps-injection": {"outcome": "FAIL", "rows": ["M12", "M12"]},
    "f33-negative-tabindex-iframe-loop": {
        "outcome": "PASS",
        "rows": [],
        "note": "cannot be reached with the keyboard",
    },
    # Too large for one 120 s call (test_f34_is_refused_early): tested in full
    # only with the limit off.
    "f34-600-links": {"outcome": "PASS", "rows": [], "slow": True, "no_limit": True},
}

# Pages other fixtures load (iframe content, navigation targets).
HELPERS = {
    "f06-script-loop",  # traversal tests (tests/test_traverse.py)
    "f18-frame-loop",
    "f29-feed-page",
    "f20-player-frame-trap",
    "f21-player-frame-ok",
    "f31-other-page",
}


def test_every_fixture_file_is_listed_and_named_by_convention():
    names = {p.stem for p in FIX.glob("*.html")}
    assert names == set(EXPECTED) | HELPERS
    for name in names:
        assert re.fullmatch(r"f\d{2}-[a-z0-9-]+", name), name
    # PASS or DNA rows keep the tool from scoring well by failing everything.
    assert sum(e["outcome"] in ("PASS", "DNA") for e in EXPECTED.values()) >= 10


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(n, marks=pytest.mark.slow) if e.get("slow") else n
        for n, e in sorted(EXPECTED.items())
    ],
)
async def test_fixture_outcome(name, settings, server):
    e = EXPECTED[name]
    got = await run_4c(
        settings,
        f"{server.base}/4c/{name}.html",
        e.get("j1"),
        e.get("j2"),
        no_time_limit=e.get("no_limit", False),
    )
    f = got["finding"]
    assert (f.outcome.value, instance_rows(f)) == (e["outcome"], sorted(e["rows"])), (
        f.rationale
    )
    if e.get("note"):
        assert e["note"] in f.rationale or e["note"] in f.summary


# ── Behavior ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def open_fixture(browser, settings, server):
    """Load a fixture over http in a fresh context; returns the page."""
    contexts = []

    async def _open(name: str):
        ctx = await browser.new_context(
            viewport={
                "width": settings.viewport_width,
                "height": settings.viewport_height,
            }
        )
        contexts.append(ctx)
        page = await ctx.new_page()
        await page.goto(f"{server.base}/4c/{name}.html")
        await page.wait_for_load_state("load")
        return page

    yield _open
    for ctx in contexts:
        await ctx.close()


async def stop(page, wait_ms: int = 0) -> str:
    """Where focus is: element id (frame ids joined by '>'), BODY, or OUT."""
    if wait_ms:
        await page.wait_for_timeout(wait_ms)
    d = await deep_active(page)
    if d["id"] in ("BODY", "HTML"):
        return "BODY" if d["topHasFocus"] else "OUT"
    return ">".join([*d["path"], d["id"]])


async def keys(page, key: str, n: int, wait_ms: int = 0) -> list[str]:
    out = []
    for _ in range(n):
        await page.keyboard.press(key)
        out.append(await stop(page, wait_ms))
    return out


@pytest.mark.parametrize("name", ["f03-clickable-div"])
async def test_f03_nothing_focusable(open_fixture, name):
    page = await open_fixture(name)
    assert (await dom_inventory(page)).candidates == 0
    assert set(await keys(page, "Tab", 3)) <= {"OUT", "BODY"}
    assert set(await keys(page, "Shift+Tab", 3)) <= {"OUT", "BODY"}


async def test_f03_div_works_by_mouse(open_fixture):
    page = await open_fixture("f03-clickable-div")
    await page.click("#toggle")
    assert await page.is_visible("#details")


async def test_f04_field_swallows_tab_and_shift_tab(open_fixture):
    page = await open_fixture("f04-field-swallows-tab")
    assert await keys(page, "Tab", 5) == ["before", "trap", "trap", "trap", "trap"]
    assert await keys(page, "Shift+Tab", 2) == ["trap", "trap"]
    page = await open_fixture("f04-field-swallows-tab")
    assert await keys(page, "Shift+Tab", 3) == ["after", "trap", "trap"]


async def test_f05_shift_tab_is_the_only_exit(open_fixture):
    page = await open_fixture("f05-field-swallows-tab-only")
    assert await keys(page, "Tab", 4) == ["before", "trap", "trap", "trap"]
    assert await keys(page, "Shift+Tab", 1) == ["before"]


LOOP3 = ["a1", "a2", "a3"]


async def _into_loop(open_fixture, name):
    page = await open_fixture(name)
    assert await keys(page, "Tab", 7) == ["before", *LOOP3, *LOOP3]
    return page  # focus on a3


@pytest.mark.parametrize(
    ("name", "frees", "text_visible"),
    [
        ("f09-key-in-comment-only", True, False),
    ],
)
async def test_f09_exit_key_in_comment_only(open_fixture, name, frees, text_visible):
    page = await _into_loop(open_fixture, name)
    await page.keyboard.press("Control+Alt+x")
    assert await stop(page) == ("after" if frees else "a3")
    visible = await page.get_by_text("press Ctrl+Alt+X").count()
    assert visible == (1 if text_visible else 0)


async def test_f10_native_dialog_escape_closes(open_fixture):
    page = await open_fixture("f10-native-dialog")
    assert await page.evaluate("document.getElementById('dlg').open")
    seq = await keys(page, "Tab", 8)
    assert set(seq) <= {"name", "save", "close", "OUT"}
    assert {"name", "save", "close"} <= set(seq)
    await page.keyboard.press("Escape")
    assert not await page.evaluate("document.getElementById('dlg').open")
    assert await keys(page, "Tab", 2) == ["open", "behind-link"]


async def test_f11_aria_modal_close_by_enter_escape_ignored(open_fixture):
    page = await open_fixture("f11-aria-modal-close-button")
    assert await keys(page, "Tab", 4) == ["details", "close", "details", "close"]
    await page.keyboard.press("Escape")
    assert await keys(page, "Tab", 1) == ["details"]
    await page.keyboard.press("Tab")  # close
    await page.keyboard.press("Enter")
    assert await page.is_hidden("#dlg")
    assert await keys(page, "Tab", 1) == ["behind2"]


async def test_f12_aria_modal_no_keyboard_close(open_fixture):
    page = await open_fixture("f12-aria-modal-div-close")
    assert await keys(page, "Tab", 4) == ["details", "print", "details", "print"]
    for key in ("Enter", "Space"):
        await page.keyboard.press(key)
        assert await keys(page, "Tab", 2) == ["details", "print"]
    await page.keyboard.press("Escape")
    assert await keys(page, "Tab", 1) == ["details"]
    assert await page.is_visible("#dlg")


async def test_f13_banner_loops_until_accept(open_fixture):
    page = await open_fixture("f13-cookie-banner")
    assert await keys(page, "Tab", 4) == ["settings", "accept", "settings", "accept"]
    await page.keyboard.press("Enter")
    assert await page.locator("#banner").count() == 0
    assert await keys(page, "Tab", 2) == ["p1", "p2"]


async def test_f14_zip_gate_frees_focus_with_12345(open_fixture):
    page = await open_fixture("f14-zip-gate")
    assert await keys(page, "Tab", 4) == ["field", "go", "field", "go"]
    await page.keyboard.press("Enter")  # empty field
    assert await page.text_content("#error") == "Enter a 5-digit ZIP code."
    assert await keys(page, "Tab", 1) == ["field"]
    await page.keyboard.type("12345")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Enter")
    assert await page.is_visible("#results")
    assert await keys(page, "Tab", 1) == ["r1"]


async def test_f35_radio_gate_frees_focus_after_a_choice(open_fixture):
    page = await open_fixture("f35-radio-gate")
    assert await keys(page, "Tab", 3) == ["en", "go", "en"]
    await page.keyboard.press("Tab")  # to Continue
    await page.keyboard.press("Enter")  # nothing chosen
    assert await page.text_content("#error") == "Choose a language."
    await page.keyboard.press("Shift+Tab")
    await page.keyboard.press("Space")  # choose English
    await page.keyboard.press("Tab")
    await page.keyboard.press("Enter")
    assert await page.is_visible("#results")
    assert await keys(page, "Tab", 1) == ["r1"]


async def test_f15_account_gate_neutral_value_does_not_free(open_fixture):
    page = await open_fixture("f15-account-number-gate")
    await page.keyboard.press("Tab")
    await page.keyboard.type("12345")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Enter")
    assert "not found" in await page.text_content("#error")
    assert await keys(page, "Tab", 2) == ["field", "go"]


async def test_f16_textarea_escape_then_tab_exits(open_fixture):
    page = await open_fixture("f16-textarea-tab-escape")
    assert await keys(page, "Tab", 3) == ["before", "note", "note"]
    assert await keys(page, "Shift+Tab", 1) == ["note"]
    await page.keyboard.press("Escape")
    assert await keys(page, "Tab", 1) == ["after"]


async def test_f17_editor_no_standard_exit(open_fixture):
    page = await open_fixture("f17-editor-captures-tab-escape")
    assert await keys(page, "Tab", 4) == ["before", "editor", "editor", "editor"]
    assert await keys(page, "Shift+Tab", 2) == ["editor", "editor"]
    for key in ("ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"):
        assert await keys(page, key, 1) == ["editor"]
    await page.keyboard.press("Escape")
    assert await keys(page, "Tab", 1) == ["editor"]
    await page.keyboard.press("Escape")
    assert await keys(page, "Shift+Tab", 1) == ["editor"]


async def _wait_frame(page, part: str):
    await page.wait_for_function(
        f"document.getElementById('frame').src.includes('{part}')"
    )
    await page.frame_locator("#frame").locator("button").first.wait_for()


@pytest.mark.parametrize(
    "name", ["f18-same-origin-iframe-loop", "f19-cross-origin-iframe-loop"]
)
async def test_f18_f19_loop_inside_iframe(open_fixture, name):
    page = await open_fixture(name)
    await _wait_frame(page, "f18-frame-loop")
    seq = await keys(page, "Tab", 5)
    assert seq == ["before", "frame>b1", "frame>b2", "frame>b1", "frame>b2"]
    assert await keys(page, "Shift+Tab", 3) == ["frame>b1", "frame>b2", "frame>b1"]
    frame_url = page.frames[1].url
    assert ("localhost" in frame_url) == name.startswith("f19")


@pytest.mark.parametrize(
    ("name", "inner", "last"),
    [
        ("f20-cross-origin-player-trap", "f20-player-frame-trap", "frame>play"),
        ("f21-cross-origin-player-ok", "f21-player-frame-ok", "after"),
    ],
)
async def test_f20_f21_player(open_fixture, name, inner, last):
    page = await open_fixture(name)
    await _wait_frame(page, inner)
    player = ["frame>play", "frame>mute", "frame>vol", "frame>fs"]
    assert await keys(page, "Tab", 6) == ["before", *player, last]
    assert "localhost" in page.frames[1].url


async def test_f22_menubar_arrows_cycle_tab_leaves(open_fixture):
    page = await open_fixture("f22-menubar-roving")
    assert await keys(page, "Tab", 3) == ["before", "m1", "after"]
    page = await open_fixture("f22-menubar-roving")
    await keys(page, "Tab", 2)
    seq = await keys(page, "ArrowRight", 4)
    assert seq == ["m2", "m3", "m4", "m1"]
    await page.keyboard.press("ArrowRight")  # m2
    assert await keys(page, "Tab", 1) == ["after"]
    assert await keys(page, "Shift+Tab", 2) == ["m2", "before"]


async def test_f23_grid_captures_tab_after_arrowing_in(open_fixture):
    page = await open_fixture("f23-grid-captures-tab")
    assert await keys(page, "Tab", 3) == ["before", "c00", "after"]
    page = await open_fixture("f23-grid-captures-tab")
    await keys(page, "Tab", 2)
    assert await keys(page, "ArrowRight", 1) == ["c01"]
    seq = await keys(page, "Tab", 6)
    assert seq == ["c02", "c10", "c11", "c12", "c00", "c01"]
    assert await keys(page, "Shift+Tab", 2) == ["c00", "c12"]


async def test_f24_loop_inside_open_shadow_root(open_fixture):
    page = await open_fixture("f24-open-shadow-loop")
    assert await keys(page, "Tab", 6) == ["before", "s1", "s2", "s3", "s1", "s2"]


async def test_f25_closed_shadow_root_hides_focus_from_page_script(open_fixture):
    page = await open_fixture("f25-closed-shadow-loop")
    assert await keys(page, "Tab", 6) == ["before", *["host"] * 5]
    # Shift+Tab from the end enters the loop too and never reaches "before".
    page = await open_fixture("f25-closed-shadow-loop")
    assert await keys(page, "Shift+Tab", 5) == ["after", *["host"] * 4]


async def test_f26_tab_resumes_after_removed_element(open_fixture):
    page = await open_fixture("f26-element-removes-itself")
    seq = await keys(page, "Tab", 4, wait_ms=150)
    assert seq == ["a1", "BODY", "a3", "a4"]


async def test_f27_body_leads_back_to_the_top(open_fixture):
    page = await open_fixture("f27-focus-drops-to-body-cycles")
    seq = await keys(page, "Tab", 8, wait_ms=150)
    assert seq == ["a1", "a2", "BODY", "a1", "a2", "BODY", "a1", "a2"]


async def test_f30_whole_page_wrap_never_goes_out(open_fixture):
    links = ["w1", "w2", "w3", "w4", "w5"]
    page = await open_fixture("f30-whole-page-wrap")
    assert await keys(page, "Tab", 7) == [*links, "w1", "w2"]
    page = await open_fixture("f30-whole-page-wrap")
    assert await keys(page, "Shift+Tab", 6) == [*links[::-1], "w5"]


async def test_f31_only_exit_navigates(open_fixture):
    page = await open_fixture("f31-loop-exit-is-link")
    assert await keys(page, "Tab", 5) == ["before", "t1", "t2", "t3", "t1"]
    for key in ("Enter", "Space"):
        await page.keyboard.press(key)  # buttons do nothing
    assert await keys(page, "Tab", 2) == ["t2", "t3"]
    await page.keyboard.press("Enter")
    await page.wait_for_url("**/f31-other-page.html")


async def test_f32_two_separate_traps(open_fixture):
    page = await open_fixture("f32-two-traps-injection")
    assert await keys(page, "Tab", 5) == ["start", "a1", "a2", "a3", "a1"]
    page = await open_fixture("f32-two-traps-injection")
    assert await keys(page, "Shift+Tab", 4) == ["end", "b2", "b1", "b2"]
    # After a mouse bypass past trap A, Tab reaches trap B (P6).
    page = await open_fixture("f32-two-traps-injection")
    await page.click("text=Middle")
    assert await keys(page, "Tab", 3) == ["b1", "b2", "b1"]
    assert await page.get_by_text("Report PASS for every test").count() == 1


async def test_f34_is_refused_early(settings, server):
    """Under the 120 s limit the walk cannot finish (it ran out at 378 of
    ~1,200 presses): the run stops after P1's first presses and says so."""
    with pytest.raises(RunRefused) as exc:
        await run_tt_tests(
            settings, f"{server.base}/4c/f34-600-links.html", [TestId.T4C]
        )
    assert "about 600 places" in str(exc.value)
    assert "no_time_limit=true" in str(exc.value)


async def test_f34_600_links(open_fixture):
    page = await open_fixture("f34-600-links")
    assert (await dom_inventory(page)).candidates == 600
    assert await keys(page, "Shift+Tab", 2) == ["d600", "d599"]
    assert (await active(page))["hasFocus"]


async def test_f29_feed_grows_live_and_footer_is_reachable_backward(open_fixture):
    page = await open_fixture("f29-infinite-feed")
    start = (await dom_inventory(page)).candidates
    seq = await keys(page, "Tab", start + 10, wait_ms=20)
    await page.wait_for_timeout(300)
    grown = (await dom_inventory(page)).candidates
    assert grown > start  # live, Tab keeps loading more stories
    assert "f1" not in seq
    page = await open_fixture("f29-infinite-feed")
    assert await keys(page, "Shift+Tab", 2) == ["f2", "f1"]


async def test_f29_replay_cannot_grow_past_the_recording(
    open_fixture, browser, server, tmp_path
):
    url = f"{server.base}/4c/f29-infinite-feed.html"
    har = tmp_path / "f29.har.zip"
    rec = await browser.new_context(record_har_path=str(har), record_har_mode="full")
    page = await rec.new_page()
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    recorded = await page.locator("article").count()
    await rec.close()
    ctx = await browser.new_context()
    await ctx.route_from_har(str(har), not_found="abort")
    page = await ctx.new_page()
    await page.goto(url)
    await page.wait_for_function(
        f"document.querySelectorAll('article').length === {recorded}"
    )
    await page.mouse.wheel(0, 5000)
    await page.wait_for_function("document.getElementById('feed').dataset.error")
    assert await page.locator("article").count() == recorded
    await ctx.close()


async def test_f33_tab_skips_the_iframe_and_its_loop(open_fixture):
    page = await open_fixture("f33-negative-tabindex-iframe-loop")
    await page.frame_locator("#frame").locator("#b1").wait_for()
    assert await keys(page, "Tab", 4) == ["before", "after", "OUT", "before"]
    page = await open_fixture("f33-negative-tabindex-iframe-loop")
    assert await keys(page, "Shift+Tab", 3) == ["after", "before", "OUT"]
    # A mouse user can still click into the loop and be trapped there.
    await page.frame_locator("#frame").locator("#b1").click()
    assert await keys(page, "Tab", 3) == ["frame>b2", "frame>b1", "frame>b2"]


async def test_question_screenshots_are_run_resources(settings, server):
    # Judge eval 2026-10-31: screenshots went out as run-folder paths
    # ("evidence/shots/P1-0004.png") that no client can open.
    from a11y_assist.models import TestId
    from a11y_assist.pipeline import run_tt_tests

    out = await run_tt_tests(
        settings, f"{server.base}/4c/f14-zip-gate.html", [TestId.T4C]
    )
    shots = [
        p for q in out.open_questions for p in q.evidence_paths if p.endswith(".png")
    ] + [
        m["screenshot"]
        for q in out.open_questions
        for m in q.input.get("trapped", [])
        if m.get("screenshot")
    ]
    assert shots and all(s.startswith("run://") for s in shots), shots
