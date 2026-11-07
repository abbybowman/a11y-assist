"""3.A's rows and sentences on hand-built states (no browser): the cases no
fixture page triggers reliably, and the SCRT export of NOT TESTED."""

from __future__ import annotations

from tobi508 import flash, scrt
from tobi508.checks import t3a
from tobi508.flashcap import Source, Unmeasured
from tobi508.models import Outcome

from .harness_4c import assert_plain
from .test_scrt import _report, _run_dir


def kind(peak=0, area=0, over=None) -> flash.Kind:
    return flash.Kind(
        peak=peak, area=area, over=area > flash.AREA_LIMIT if over is None else over
    )


def src(kind_="page", general=None, red=None, red22=None, boxes=None, **kw) -> Source:
    a = flash.Analysis(
        frames=180,
        span_ms=3000,
        general=general or kind(),
        red=red or kind(),
        red22=red22 or kind(),
        boxes=boxes if boxes is not None else [[0, 60, 100, 100]],
    )
    return Source(kind=kind_, analysis=a, **kw)


def evaluate(st):
    f = t3a.evaluate(st, [])
    assert_plain(f.summary)
    return f


def test_pass_t_failed_is_not_performed():
    f = evaluate(t3a.State3A(motion_ok=False, error="the page could not be loaded"))
    assert f.outcome is Outcome.NEEDS_REVIEW and f.rows == ["A1"]


def test_nothing_triggered_does_not_apply():
    f = evaluate(t3a.State3A())
    assert f.outcome is Outcome.DNA and f.rows == ["A4"]


def test_unmeasured_is_not_performed_and_named():
    st = t3a.State3A(
        unmeasured=[Unmeasured(what="a video", why="its file is larger than we record")]
    )
    f = evaluate(st)
    assert f.outcome is Outcome.NEEDS_REVIEW and f.rows == ["A3"]
    assert "its file is larger than we record" in f.summary


def test_flashing_beats_unmeasured():
    st = t3a.State3A(
        sources=[src(general=kind(10, 1600))],
        unmeasured=[Unmeasured(what="a video", why="it streams")],
    )
    f = evaluate(st)
    assert f.outcome is Outcome.NOT_TESTED and f.rows == ["A2", "s1:F5"]
    assert "does not fail WCAG 2.3.1" in f.summary


def test_a_video_analyzed_in_part():
    v = src("video", general=kind(2, 0), analyzed_s=9.97, length_s=150.0)
    f = evaluate(t3a.State3A(sources=[v]))
    assert f.outcome is Outcome.NEEDS_REVIEW
    assert "a video after its first 10 seconds" in f.summary
    # With flashing found, the note says how much was analyzed (O4).
    v2 = src("video", general=kind(10, 1600), analyzed_s=9.97, length_s=150.0)
    f = evaluate(t3a.State3A(sources=[v2]))
    assert f.outcome is Outcome.NOT_TESTED
    assert "We analyzed the first 10 s of 150 s." in f.summary


def test_screencast_only_flashing_is_not_measured():
    sc = flash.Analysis(general=kind(12, 50_000))
    f = evaluate(t3a.State3A(screencast=sc, sources=[src()]))
    assert f.rows == ["A3"] and "while we watched" in f.summary
    # Within one transition of what the capture counted: its jitter.
    sc = flash.Analysis(general=kind(7, 50_000))
    f = evaluate(t3a.State3A(screencast=sc, sources=[src(general=kind(6, 0))]))
    assert f.rows == ["A4"]


def test_failing_part_decides_before_a_fine_pattern():
    s = src(general=kind(10, 30_000))
    s.analysis.fine = True
    assert t3a.assess(s, 0, set()) == "F2"
    s2 = src(general=kind(0, 0))
    s2.analysis.fine, s2.analysis.fine_pixels = True, 40
    assert t3a.assess(s2, 0, set()) == "F1"


def test_red_rows_and_the_22_note():
    s = src(red=kind(10, 30_000), red22=kind(10, 30_000))
    assert t3a.assess(s, 0, set()) == "F3"
    assert t3a.assess22(s, "F3") is None
    s = src(red=kind(10, 30_000), red22=kind(0, 0))
    f = evaluate(t3a.State3A(sources=[s]))
    assert "Under WCAG 2.2's definition of a red flash it would not fail." in f.summary
    s = src(general=kind(10, 1600), red22=kind(10, 30_000))
    assert t3a.assess22(s, "F5") == "would fail"


def test_together_needs_one_rectangle_and_enough_area():
    a = src(general=kind(10, 12_000), boxes=[[0, 60, 120, 100]])
    b = src("image", general=kind(10, 12_000), boxes=[[140, 60, 120, 100]])
    far = src("image", general=kind(10, 12_000), boxes=[[700, 60, 120, 100]])
    small = src("image", general=kind(10, 4_000), boxes=[[140, 60, 40, 100]])
    vid = src("video", general=kind(10, 12_000), boxes=[[140, 60, 120, 100]])
    assert t3a.together([a, b]) == {0, 1}
    assert t3a.together([a, far]) == set()
    assert t3a.together([a, small]) == set()
    assert t3a.together([a, vid]) == set()  # a video is analyzed full screen


def test_page_assessment_is_the_worst_source():
    fails = src(general=kind(10, 30_000))
    fine = src("image", general=kind(0, 0), boxes=[[600, 400, 50, 50]])
    fine.analysis.fine = True
    f = evaluate(t3a.State3A(sources=[fails, fine]))
    assert "fails WCAG 2.3.1" in f.summary and f.rows == ["A2", "s1:F2", "s2:F1"]


def test_triggers_from_pass_t():
    from tobi508.motion import Media, MotionPass

    mp = MotionPass(
        fast_animations=[{"frame": 0, "css": "#a", "name": "f", "per_s": 10}],
        fast_callbacks=[
            {"frame": 0, "t": k * 0.08, "kind": "interval"} for k in range(20)
        ]
        + [{"frame": 0, "t": k * 0.5, "kind": "raf"} for k in range(5)],
        animated_images=[
            {"src": "http://x/a.gif", "min_ms": 100},
            {"src": "http://x/b.gif", "min_ms": 500},
        ],
        media=[
            Media(
                frame=0,
                at=0,
                css="video",
                tag="video",
                paused=False,
                muted=True,
                volume=1,
                time=0.0,
            ),
            Media(
                frame=0,
                at=3.5,
                css="video",
                tag="video",
                paused=False,
                muted=True,
                volume=1,
                time=3.4,
            ),
        ],
        iframes=["https://www.youtube.com/embed/x?autoplay=1"],
    )
    got, gone = t3a.triggers(mp)
    assert sorted(t.kind for t in got) == ["animation", "image", "timer", "video"]
    assert [u.what for u in gone] == ["a video player from another site"]


def test_scrt_keeps_not_tested_and_the_assessment(tmp_path):
    f = evaluate(t3a.State3A(sources=[src(general=kind(10, 30_000))]))
    doc = scrt.from_report(_report([f]), _run_dir(tmp_path))
    [row] = doc.results()["3.A"]
    assert row.TestResult is scrt.ScrtResult.NOT_TESTED
    assert row.TesterComment.startswith(
        "The Trusted Tester process records flashing content as Not Tested."
    )
    assert "fails WCAG 2.3.1" in row.TesterComment
