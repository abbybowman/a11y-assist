"""3.A's counting (flash.py) on synthetic frames: no browser, fast and
deterministic (build tasks V2-V4). Expected values come from WCAG 2.0 SC
2.3.1, G19 and G176, cited per test."""

from __future__ import annotations

import numpy as np
import pytest

from tobi508 import flash

FPS = 60
BLACK, WHITE, RED = (0, 0, 0), (255, 255, 255), (255, 0, 0)


def times(n: int) -> list[float]:
    return [k * 1000 / FPS for k in range(n)]


def frames(states: list[tuple], size=(64, 64), box=None, bg=(128, 128, 128)):
    """One frame per state; `box` (x, y, w, h) is painted with the state on
    `bg`, or the whole frame when None."""
    out = []
    for s in states:
        f = np.zeros((size[1], size[0], 3), np.uint8)
        f[:] = bg
        if box is None:
            f[:] = s
        else:
            x, y, w, h = box
            f[y : y + h, x : x + w] = s
        out.append(f)
    return out


def toggles(n_frames: int, every: int, a=BLACK, b=WHITE, start: int = 0, stop=None):
    """States switching every `every` frames from `start` until `stop`."""
    out = []
    for k in range(n_frames):
        if k < start or (stop is not None and k >= stop):
            out.append(a)
        else:
            out.append(b if ((k - start) // every) % 2 else a)
    return out


def run(states, **kw):
    size = kw.pop("size", (64, 64))
    box = kw.pop("box", None)
    bg = kw.pop("bg", (128, 128, 128))
    fr = frames(states, size, box, bg)
    return flash.analyze(fr, times(len(fr)), **kw)


# ── V2: transitions and G19's boundary ─────────────────────────────────────


def test_luminance_is_wcag_20():
    lin = flash.linear(np.array([[[255, 255, 255], [0, 0, 0], [10, 10, 10]]]))
    lum = flash.luminance(lin)
    assert lum[0, 0] == pytest.approx(1.0)
    assert lum[0, 1] == 0
    # 10/255 = 0.0392 > 0.03928? No: below it, so the linear branch.
    assert lum[0, 2] == pytest.approx((10 / 255) / 12.92, rel=1e-4)


def test_six_transitions_in_a_second_is_not_flashing():
    # Exactly 3 flashes in each second, ending on the starting state (G19).
    a = run(toggles(180, 10))  # a change every 10 frames: 6 per second
    assert a.general.peak == 6
    assert not a.flashing


def test_seven_transitions_is_flashing():
    # 3.5 flashes (G19 Note 2): seven changes within one second, then still.
    st = toggles(120, 8, stop=8 * 8)  # changes at 8, 16, ..., 56
    st[64:] = [st[63]] * 56  # then holds the last state
    a = run(st)
    assert a.general.peak == 7
    assert a.flashing
    assert a.flashes_per_s == 3.5


def test_fades_count_once():
    # A ramp over 4 frames between black and white is one transition each
    # way (Note 2: between adjacent peaks and valleys).
    ramp = [tuple([v] * 3) for v in (0, 64, 128, 192, 255, 192, 128, 64)]
    a = run(ramp * 16)  # 8 frames per cycle: 2 transitions per 8 frames
    assert a.general.peak == 15  # 60 frames hold 15 transitions
    assert a.flashing


def test_small_changes_are_not_transitions():
    # Grey levels 0.08 apart in luminance: under the 0.1 general threshold.
    lo, hi = (118, 118, 118), (136, 136, 136)
    a = run(toggles(120, 2, lo, hi))
    assert not a.general.flashing


def test_light_pairs_are_not_general_flashes():
    # Both states above 0.80 luminance: the darker image is not below 0.80.
    a = run(toggles(120, 2, (235, 235, 235), WHITE))
    assert a.general.peak == 0 and not a.flashing


def test_wiggles_inside_a_state_are_not_transitions():
    # Noise of +-0.02 on top of a slow 1 per second blink stays 2.B's.
    rng = np.random.default_rng(1)
    states = []
    for k in range(180):
        base = 255 if (k // 30) % 2 else 0
        states.append(tuple([int(np.clip(base + rng.integers(-6, 7), 0, 255))] * 3))
    a = run(states)
    assert a.general.peak == 2 and not a.flashing


# ── V3: the area, inside any 341 x 256 rectangle ───────────────────────────


def test_small_flasher_flashes_under_the_area():
    # 40 x 40 at 10 per second: flashing found, 1,600 px, under 21,824 (G176).
    a = run(toggles(120, 3), size=(400, 300), box=(100, 100, 40, 40))
    assert a.flashing and a.general.area == 1600 and not a.general.over
    assert a.boxes == [[100, 100, 40, 40]]


def test_large_flasher_is_over_the_area():
    # 400 x 300: the best rectangle holds 344 x 256 cells' worth, over 21,824.
    a = run(toggles(120, 3), size=(400, 300), box=(0, 0, 400, 300))
    assert a.general.over
    # The rectangle is 341 x 256 rounded up to whole 4 px cells (344 x 256).
    assert a.general.area == 344 * 256
    assert a.general.rect[2:] == [341, 256]


def test_two_flashers_in_one_rectangle_add_up_when_in_step():
    # Each 100 x 120 = 12,000 px (under), together 24,000 inside 341 x 256,
    # changing in the same frames: over (combined area of flashes occurring
    # concurrently).
    st = toggles(120, 3)
    fr = []
    for s in st:
        f = np.full((300, 600, 3), 128, np.uint8)
        f[0:120, 0:100] = s
        f[0:120, 200:300] = s
        fr.append(f)
    a = flash.analyze(fr, times(len(fr)))
    assert a.general.area == 24_000 and a.general.over
    assert len(a.boxes) == 2


def test_two_flashers_out_of_step_do_not_add_up():
    # The same two, changing in different frames: each frame has 12,000 px
    # changing, under the area.
    s1, s2 = toggles(120, 4), toggles(120, 4, start=2)
    fr = []
    for a_, b_ in zip(s1, s2):
        f = np.full((300, 600, 3), 128, np.uint8)
        f[0:120, 0:100] = a_
        f[0:120, 200:300] = b_
        fr.append(f)
    a = flash.analyze(fr, times(len(fr)))
    assert a.flashing and a.general.area == 12_000 and not a.general.over


def test_flashers_far_apart_are_not_one_rectangle():
    # Each 160 x 160 = 25,600 alone is over; two of them 600 px apart are
    # not counted together: the area stays one flasher's.
    st = toggles(120, 3)
    fr = []
    for s in st:
        f = np.full((200, 900, 3), 128, np.uint8)
        f[0:160, 0:160] = s
        f[0:160, 700:860] = s
        fr.append(f)
    a = flash.analyze(fr, times(len(fr)))
    assert a.general.area == 25_600


def test_mask_leaves_pixels_out():
    m = np.zeros((300, 400), bool)
    m[:, :] = True
    a = run(toggles(120, 3), size=(400, 300), box=(0, 0, 400, 300), mask=m)
    assert not a.flashing


def test_scale_counts_css_pixels():
    # A video drawn at a quarter of full screen (px 4, cell 1): a 10 x 10
    # frame-pixel flasher is 40 x 40 CSS px.
    a = run(
        toggles(120, 3), size=(64, 48), box=(5, 5, 10, 10), cell=1, px=4.0, fine=False
    )
    assert a.general.area == 1600


# ── V4: red ────────────────────────────────────────────────────────────────


def test_red_to_black_is_a_red_flash_both_versions():
    a = run(toggles(120, 3, BLACK, RED))
    assert a.red.flashing and a.red22.flashing


def test_saturated_red_with_little_luminance_change():
    # Red (L 0.2126) and a grey of about the same luminance: no general
    # transition, but (R-G-B) x 320 changes by about 320 (2.0 Note 3).
    grey = (127, 127, 127)  # L about 0.212
    a = run(toggles(120, 3, grey, RED))
    assert not a.general.flashing
    assert a.red.flashing and a.red22.flashing


def test_dull_red_is_not_saturated():
    # R/(R+G+B) under 0.8 in both states: not a red transition.
    a = run(toggles(120, 3, (40, 40, 40), (200, 120, 120)))
    assert not a.red.flashing


def test_red_area_over_the_threshold():
    a = run(toggles(120, 3, BLACK, RED), size=(400, 300), box=(0, 0, 400, 300))
    assert a.red.over


# ── F1: fine patterns ──────────────────────────────────────────────────────


def checker(size: int, square: int, invert: bool) -> np.ndarray:
    y, x = np.mgrid[0:size, 0:size]
    on = ((x // square + y // square) % 2).astype(bool) ^ invert
    f = np.zeros((size, size, 3), np.uint8)
    f[on] = 255
    return f


def test_fine_checkerboard_is_found_and_marked_fine():
    # 2 px squares inverting 10 times a second: each 4 px cell keeps the
    # same average, but the pixels flash. Flashing found, as a fine pattern.
    fr = [checker(64, 2, (k // 3) % 2 == 1) for k in range(120)]
    a = flash.analyze(fr, times(120))
    assert not a.general.flashing
    assert a.fine and a.flashing


def test_coarse_checkerboard_is_not_fine():
    fr = [checker(64, 16, (k // 3) % 2 == 1) for k in range(120)]
    a = flash.analyze(fr, times(120))
    assert a.general.flashing and not a.fine


# ── Helpers ────────────────────────────────────────────────────────────────


def test_steps_are_whole_ms_summing_to_exact_sixtieths():
    s = flash.steps_ms(3)
    assert len(s) == 180 and sum(s) == 3000 and s[:3] == [17, 16, 17]


def test_resample_an_image():
    idx, t = flash.resample([100, 100], loops=2)
    assert len(idx) == 24 and idx[:7] == [0, 0, 0, 0, 0, 0, 1]
    assert t[1] == pytest.approx(1000 / 60)


def test_window_counts_half_open():
    tms = np.array(times(121))
    end = np.array([0, 10, 20, 30, 40, 50, 60])  # 60 is at exactly 1 s
    cells = np.zeros(7, np.int64)
    cand, counts = flash.window_counts(tms, end, cells, 1)
    assert counts.max() == 6  # [0, 1 s) holds 6; 1 s starts the next window
