"""Flash counting for 3.A (docs/rules/3a-flashing.md, Terms and section 3).

Pure functions on frame arrays: no browser and no outcome. The capture that
makes the frames is flashcap.py; which outcome the counts lead to is
checks/t3a.py's rows.

What is counted (WCAG 2.0 SC 2.3.1 and its Understanding page, G19, G176):
  * relative luminance with WCAG 2.0's sRGB formula (threshold 0.03928);
  * transitions: the change between a peak and the next valley of a cell's
    luminance over time (Note 2), found with a hysteresis of the transition
    size, so a fade over several frames is one transition;
  * a general transition changes by at least 0.1 with the darker state below
    0.80; a red transition (2.0 Note 3) has a state with R/(R+G+B) >= 0.8 and
    changes (R-G-B) x 320 by more than 20; WCAG 2.2's red rule (to or from
    R/(R+G+B) >= 0.8 and a CIE 1976 u'v' difference over 0.2) is counted
    too, for the note;
  * a cell flashes when more than 6 transitions (3.5 flashes, G19) end in a
    one-second window; windows start at every frame;
  * the concurrently flashing area: in one frame, the flashing cells that are
    changing, inside the best 341 x 256 rectangle (Note 1), against 21,824
    px (25%, G176);
  * fine patterns: a sample of single pixels (every other one) counted the
    same way. A pixel that flashes where no cell does is a fine, balanced
    pattern the cells average out (the WCAG exception; spec F1).

R, G and B are linear values (as for luminance) in the red rules: WCAG 2.0
does not say which, and 2.2 computes chromaticity from linear values.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np
from pydantic import BaseModel, Field

CELL = 4  # CSS px per cell side (spec Terms)
WINDOW_MS = 1000.0
GENERAL_DELTA = 0.1
DARK_MAX = 0.8
RED_RATIO = 0.8
RED_DELTA = 20.0
UV_DELTA = 0.2
MAX_TRANSITIONS = 6  # 3 flashes; a seventh transition is 3.5 (G19 Note 2)
RECT = (341, 256)  # a 10 degree field at 1024 x 768 (Note 1)
AREA_LIMIT = 21_824  # 25% of 341 x 256 (G176)
FINE_STRIDE = 2  # the pixel sample for fine patterns
EPS = 1e-6
# D65 white: the chromaticity given to black, which has none (WCAG 2.2's
# rule needs a value for it; a red-to-black strobe is a red flash).
D65_UV = (0.1978, 0.4683)
SERIES_MAX = 400  # frames kept in the plotted series


def linear(rgb: np.ndarray) -> np.ndarray:
    """sRGB 0-255 to linear 0-1 (WCAG 2.0's formula)."""
    c = rgb.astype(np.float32) / 255.0
    return np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(
        np.float32
    )


def luminance(lin: np.ndarray) -> np.ndarray:
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def blocks(a: np.ndarray, cell: int) -> np.ndarray:
    """Means of cell x cell squares (edges padded by repeating them)."""
    if cell == 1:
        return a
    h, w = a.shape[:2]
    ph, pw = -h % cell, -w % cell
    if ph or pw:
        a = np.pad(a, ((0, ph), (0, pw)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    hh, ww = a.shape[0] // cell, a.shape[1] // cell
    return a.reshape(hh, cell, ww, cell, *a.shape[2:]).mean(axis=(1, 3))


def red_values(lin: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """WCAG 2.0 Note 3: (R-G-B) x 320 with negatives set to 0, and R/(R+G+B)
    (0 for black)."""
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    total = r + g + b
    ratio = np.where(total > EPS, r / np.maximum(total, EPS), 0.0)
    return np.maximum(0.0, (r - g - b) * 320.0), ratio


def chromaticity(lin: np.ndarray) -> np.ndarray:
    """CIE 1976 u'v' from linear sRGB (D65 for black), shape (..., 2)."""
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    x = 0.4124 * r + 0.3576 * g + 0.1805 * b
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    d = x + 15 * y + 3 * z
    ok = d > EPS
    dd = np.maximum(d, EPS)
    u = np.where(ok, 4 * x / dd, D65_UV[0])
    v = np.where(ok, 9 * y / dd, D65_UV[1])
    return np.stack([u, v], axis=-1).astype(np.float32)


class _Transitions:
    """Collected transitions: the cell, the frame the change ends at (the
    first frame at the new peak or valley), the last frame at the old one,
    both values, both states' extra value (R/(R+G+B) for red), and when it
    happened: the first frame half the threshold away from the old state (a
    noisy plateau's highest frame is not when the change happened): the frame
    after the last one still within half the threshold of the old state."""

    def __init__(self) -> None:
        self.parts: list[tuple[np.ndarray, ...]] = []

    def add(self, cells, end, start, a, b, aux_a, aux_b, at) -> None:
        if len(cells):
            self.parts.append((cells, end, start, a, b, aux_a, aux_b, at))

    def arrays(self) -> tuple[np.ndarray, ...]:
        if not self.parts:
            e = np.zeros(0, np.int64)
            f = np.zeros(0, np.float32)
            return e, e, e, f, f, f, f, e
        return tuple(np.concatenate([p[i] for p in self.parts]) for i in range(8))


class Hysteresis:
    """Peaks and valleys of N series at once, one frame at a time. A peak is
    confirmed when the series falls back from it by `delta` (a valley, when
    it rises by `delta`), so the transitions found are the changes between
    adjacent peaks and valleys of at least `delta` (Note 2). `strict`: more
    than `delta` (the red rule's "> 20")."""

    def __init__(self, n: int, delta: float, strict: bool = False) -> None:
        self.n, self.delta, self.strict = n, delta, strict
        self.out = _Transitions()
        self.t = -1

    def _reach(self, x: np.ndarray) -> np.ndarray:
        return x > self.delta + EPS if self.strict else x >= self.delta - EPS

    def step(self, v: np.ndarray, aux: np.ndarray | None = None) -> None:
        v = np.asarray(v, np.float32).ravel()
        aux = (
            np.zeros(self.n, np.float32)
            if aux is None
            else np.asarray(aux, np.float32).ravel()
        )
        self.t += 1
        t = self.t
        if t == 0:
            n = self.n
            self.dir = np.zeros(n, np.int8)
            self.ext_v, self.ext_last, self.ext_aux = (
                v.copy(),
                np.zeros(n, np.int64),
                aux.copy(),
            )
            self.run_v, self.run_first = v.copy(), np.zeros(n, np.int64)
            self.run_last, self.run_aux = np.zeros(n, np.int64), aux.copy()
            self.lo_v, self.lo_last, self.lo_aux = (
                v.copy(),
                np.zeros(n, np.int64),
                aux.copy(),
            )
            self.hi_v, self.hi_first = v.copy(), np.zeros(n, np.int64)
            self.hi_last, self.hi_aux = np.zeros(n, np.int64), aux.copy()
            self.run_at = np.zeros(n, np.int64)
            self.near_last = np.zeros(n, np.int64)  # last frame near the old state
            self.up_last = np.zeros(n, np.int64)  # no direction yet: near lo
            self.down_last = np.zeros(n, np.int64)  # ... and near hi
            return
        # No direction yet: the lowest and highest values so far.
        z = self.dir == 0
        newhi = z & (v > self.hi_v + EPS)
        samehi = z & ~newhi & (np.abs(v - self.hi_v) <= EPS)
        self.hi_v[newhi], self.hi_first[newhi], self.hi_aux[newhi] = (
            v[newhi],
            t,
            aux[newhi],
        )
        self.hi_last[newhi | samehi] = t
        newlo = z & (v < self.lo_v - EPS)
        samelo = z & ~newlo & (np.abs(v - self.lo_v) <= EPS)
        self.lo_v[newlo], self.lo_aux[newlo] = v[newlo], aux[newlo]
        self.lo_last[newlo | samelo] = t
        half = self.delta / 2 - EPS
        self.up_last[z & (v - self.lo_v < half)] = t
        self.down_last[z & (self.hi_v - v < half)] = t
        go = z & self._reach(self.hi_v - self.lo_v)
        up, down = go & newhi, go & ~newhi
        for m, frm, to, d in ((up, "lo", "hi", 1), (down, "hi", "lo", -1)):
            if not m.any():
                continue
            self.dir[m] = d
            self.ext_v[m] = getattr(self, frm + "_v")[m]
            self.ext_last[m] = getattr(self, frm + "_last")[m]
            self.ext_aux[m] = getattr(self, frm + "_aux")[m]
            self.run_v[m] = getattr(self, to + "_v")[m]
            self.run_first[m] = self.hi_first[m] if to == "hi" else t
            self.run_last[m] = getattr(self, to + "_last")[m]
            self.run_aux[m] = getattr(self, to + "_aux")[m]
            self.run_at[m] = (self.up_last if d == 1 else self.down_last)[m] + 1
            self.near_last[m] = t
        # Rising (or falling): extend the run; a fall (rise) of delta from it
        # confirms the transition into it.
        rev = np.zeros(self.n, bool)
        for d in (1, -1):
            p = (self.dir == d) & ~go
            if not p.any():
                continue
            more = p & ((v > self.run_v + EPS) if d == 1 else (v < self.run_v - EPS))
            same = p & ~more & (np.abs(v - self.run_v) <= EPS)
            self.run_v[more], self.run_first[more], self.run_aux[more] = (
                v[more],
                t,
                aux[more],
            )
            self.run_last[more | same] = t
            back = (self.run_v - v) if d == 1 else (v - self.run_v)
            self.near_last[p & (back < half)] = t
            rev |= p & self._reach(back)
        if rev.any():
            self._confirm(rev)
            self.ext_v[rev], self.ext_last[rev] = self.run_v[rev], self.run_last[rev]
            self.ext_aux[rev] = self.run_aux[rev]
            self.run_v[rev], self.run_first[rev], self.run_last[rev] = v[rev], t, t
            self.run_aux[rev] = aux[rev]
            self.run_at[rev] = self.near_last[rev] + 1
            self.near_last[rev] = t
            self.dir[rev] = -self.dir[rev]

    def _confirm(self, m: np.ndarray) -> None:
        cells = np.nonzero(m)[0]
        self.out.add(
            cells,
            self.run_first[cells].copy(),
            self.ext_last[cells].copy(),
            self.ext_v[cells].copy(),
            self.run_v[cells].copy(),
            self.ext_aux[cells].copy(),
            self.run_aux[cells].copy(),
            self.run_at[cells].copy(),
        )

    def finish(self) -> tuple[np.ndarray, ...]:
        """The transitions, the last one included when the series ends at a
        new peak or valley."""
        if self.t >= 0:
            m = (self.dir != 0) & self._reach(np.abs(self.run_v - self.ext_v))
            if m.any():
                self._confirm(m)
        return self.out.arrays()


class Hysteresis2D:
    """WCAG 2.2's red rule on u'v' chromaticity: a change to a state more
    than `delta` away from the last one, through its farthest point. For the
    note only (2.0 decides the assessment)."""

    def __init__(self, n: int, delta: float = UV_DELTA) -> None:
        self.n, self.delta = n, delta
        self.out = _Transitions()
        self.t = -1

    def step(self, uv: np.ndarray, aux: np.ndarray) -> None:
        uv = np.asarray(uv, np.float32).reshape(self.n, 2)
        aux = np.asarray(aux, np.float32).ravel()
        self.t += 1
        t = self.t
        if t == 0:
            n = self.n
            self.anc, self.anc_last, self.anc_aux = (
                uv.copy(),
                np.zeros(n, np.int64),
                aux.copy(),
            )
            self.moving = np.zeros(n, bool)
            self.run, self.run_first, self.run_last = (
                uv.copy(),
                np.zeros(n, np.int64),
                np.zeros(n, np.int64),
            )
            self.run_aux, self.run_d = aux.copy(), np.zeros(n, np.float32)
            return
        da = np.linalg.norm(uv - self.anc, axis=1)
        still = ~self.moving
        self.anc_last[still & (da <= EPS)] = t
        start = still & (da > self.delta + EPS)
        mv = self.moving.copy()
        farther = mv & (da > self.run_d + EPS)
        for m in (start, farther):
            self.run[m], self.run_first[m], self.run_last[m] = uv[m], t, t
            self.run_aux[m], self.run_d[m] = aux[m], da[m]
        self.moving |= start
        dr = np.linalg.norm(uv - self.run, axis=1)
        self.run_last[mv & ~farther & (dr <= EPS)] = t
        rev = mv & ~farther & (dr > self.delta + EPS)
        if rev.any():
            self._confirm(rev)
            self.anc[rev], self.anc_last[rev] = self.run[rev], self.run_last[rev]
            self.anc_aux[rev] = self.run_aux[rev]
            self.run[rev], self.run_first[rev], self.run_last[rev] = uv[rev], t, t
            self.run_aux[rev], self.run_d[rev] = aux[rev], dr[rev]

    def _confirm(self, m: np.ndarray) -> None:
        cells = np.nonzero(m)[0]
        zero = np.zeros(len(cells), np.float32)
        self.out.add(
            cells,
            self.run_first[cells].copy(),
            self.anc_last[cells].copy(),
            zero,
            zero,
            self.anc_aux[cells].copy(),
            self.run_aux[cells].copy(),
            self.run_first[cells].copy(),
        )

    def finish(self) -> tuple[np.ndarray, ...]:
        if self.t >= 0 and self.moving.any():
            self._confirm(self.moving)
        return self.out.arrays()


class Kind(BaseModel):
    """One kind of flash (general, red, or WCAG 2.2's red) in one analysis."""

    peak: int = 0  # most transitions of any one cell in a one-second window
    flashing_cells: int = 0  # cells with more than 6 in some window
    area: int = 0  # largest concurrently flashing area, CSS px
    rect: list[int] = Field(default_factory=list)  # its 341 x 256 rectangle
    at_ms: float | None = None  # the start of that one-second window
    over: bool = False  # area over 21,824 px

    @property
    def flashing(self) -> bool:
        return self.peak > MAX_TRANSITIONS


class Analysis(BaseModel):
    """What one sequence of frames shows (spec section 6)."""

    frames: int = 0
    span_ms: float = 0.0
    general: Kind = Field(default_factory=Kind)
    red: Kind = Field(default_factory=Kind)  # WCAG 2.0 Note 3
    red22: Kind = Field(default_factory=Kind)  # WCAG 2.2 (the note only)
    fine: bool = False  # pixels flash where no cell does (F1)
    fine_pixels: int = 0
    boxes: list[list[int]] = Field(default_factory=list)  # where, CSS px
    series: list[float] = Field(default_factory=list)  # busiest cell's L
    series_box: list[int] = Field(default_factory=list)

    @property
    def flashing(self) -> bool:
        return self.general.flashing or self.red.flashing or self.fine

    @property
    def flashes_per_s(self) -> float:
        return max(self.general.peak, self.red.peak) / 2


def window_counts(
    times: np.ndarray,
    end: np.ndarray,
    cells: np.ndarray,
    n_cells: int,
    min_total: int = MAX_TRANSITIONS,
) -> tuple[np.ndarray, np.ndarray]:
    """Transitions ending in each one-second window [t_s, t_s + 1 s), for the
    cells with more than `min_total` in all (only they can flash): (those
    cells, counts of shape (frames, cells))."""
    tot = np.bincount(cells, minlength=n_cells) if len(cells) else np.zeros(n_cells)
    cand = np.nonzero(tot > min_total)[0]
    nt = len(times)
    if not len(cand):
        return cand, np.zeros((nt, 0), np.int32)
    col = np.full(n_cells, -1, np.int64)
    col[cand] = np.arange(len(cand))
    keep = col[cells] >= 0
    ev = np.zeros((nt + 1, len(cand)), np.int32)
    np.add.at(ev, (end[keep] + 1, col[cells[keep]]), 1)
    cum = np.cumsum(ev, axis=0)  # cum[t]: ends at frames before t
    stop = np.searchsorted(times, times + WINDOW_MS - 1e-6, side="left")
    return cand, cum[stop] - cum[:nt]


def best_rect(ys: np.ndarray, xs: np.ndarray, rh: int, rw: int) -> tuple[int, int, int]:
    """The most points (cells) inside any rh x rw rectangle: (count, y, x)
    of its top left cell."""
    if not len(ys):
        return 0, 0, 0
    y0, x0 = int(ys.min()), int(xs.min())
    h, w = int(ys.max()) - y0 + 1, int(xs.max()) - x0 + 1
    if h <= rh and w <= rw:
        return len(ys), y0, x0
    g = np.zeros((h + 1, w + 1), np.int32)
    np.add.at(g, (ys - y0 + 1, xs - x0 + 1), 1)
    ii = g.cumsum(0).cumsum(1)
    hh, ww = min(rh, h), min(rw, w)
    s = ii[hh:, ww:] - ii[:-hh, ww:] - ii[hh:, :-ww] + ii[:-hh, :-ww]
    i, j = np.unravel_index(int(np.argmax(s)), s.shape)
    return int(s[i, j]), y0 + int(i), x0 + int(j)


def _kind(
    times: np.ndarray,
    tr: tuple[np.ndarray, ...],
    ok: np.ndarray,
    grid: tuple[int, int],
    cell_px: float,
    origin: tuple[float, float],
) -> tuple[Kind, np.ndarray]:
    """Counts and area for the qualifying transitions `ok` of one kind.
    Returns the Kind and the flashing cells (flat indices)."""
    cells, end, start, at = tr[0][ok], tr[1][ok], tr[2][ok], tr[7][ok]
    gh, gw = grid
    cand, counts = window_counts(times, at, cells, gh * gw)
    k = Kind()
    if not len(cand):
        if len(cells):  # the peak for the record, from the busiest cells
            tot = np.bincount(cells, minlength=gh * gw)
            top = max(1, int(tot.max()) - 1)
            _, few = window_counts(times, at, cells, gh * gw, top - 1)
            k.peak = int(few.max()) if few.size else 0
        return k, np.zeros(0, np.int64)
    k.peak = int(counts.max())
    flash = counts > MAX_TRANSITIONS  # (frames, cand)
    union = cand[flash.any(axis=0)]
    k.flashing_cells = len(union)
    if not len(union):
        return k, union
    # Changing: frames after the old peak (valley) up to the new one, for
    # transitions of candidate cells.
    nt = len(times)
    col = np.full(gh * gw, -1, np.int64)
    col[cand] = np.arange(len(cand))
    keep = col[cells] >= 0
    c2, e2, s2 = col[cells[keep]], end[keep], start[keep]
    changing = np.zeros((nt, len(cand)), bool)
    span = int((e2 - s2).max()) if len(e2) else 0
    for d in range(1, span + 1):
        m = s2 + d <= e2
        changing[s2[m] + d, c2[m]] = True
    rh = math.ceil(RECT[1] / cell_px)
    rw = math.ceil(RECT[0] / cell_px)
    unit = cell_px * cell_px
    seen: dict[bytes, tuple[np.ndarray, set[int]]] = {}
    stop = np.searchsorted(times, times + WINDOW_MS - 1e-6, side="left")
    for s in range(nt):
        f = flash[s]
        if not f.any():
            continue
        key = np.packbits(f).tobytes()
        frames = seen.setdefault(key, (f, set()))[1]
        frames.update(range(s, int(stop[s])))
    best = (0, 0, 0, None)
    for f, frames in seen.values():
        for t in sorted(frames):
            on = f & changing[t]
            n = int(on.sum())
            if n <= best[0]:
                continue
            flat = cand[on]
            got, y, x = best_rect(flat // gw, flat % gw, rh, rw)
            if got > best[0]:
                best = (got, y, x, t)
    if best[3] is not None:
        k.area = int(round(best[0] * unit))
        k.rect = [
            int(round(origin[0] + best[2] * cell_px)),
            int(round(origin[1] + best[1] * cell_px)),
            RECT[0],
            RECT[1],
        ]
        # The window that made it: the first flashing window holding frame t.
        t = best[3]
        for s in range(nt):
            if s <= t < stop[s] and flash[s].any():
                k.at_ms = round(float(times[s] - times[0]), 1)
                break
        k.over = k.area > AREA_LIMIT
    return k, union


def _boxes(
    cells: np.ndarray, grid: tuple[int, int], cell_px: float, origin
) -> list[list[int]]:
    """Places that flash: groups of touching flashing cells (8 neighbours),
    largest first, as x, y, width, height in CSS px."""
    gh, gw = grid
    left = {(int(c) // gw, int(c) % gw) for c in cells}
    out = []
    while left and len(out) < 10:
        start = left.pop()
        group, todo = [start], [start]
        while todo:
            y, x = todo.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    n = (y + dy, x + dx)
                    if n in left:
                        left.remove(n)
                        group.append(n)
                        todo.append(n)
        ys = [g[0] for g in group]
        xs = [g[1] for g in group]
        out.append(
            (
                len(group),
                [
                    int(round(origin[0] + min(xs) * cell_px)),
                    int(round(origin[1] + min(ys) * cell_px)),
                    int(round((max(xs) - min(xs) + 1) * cell_px)),
                    int(round((max(ys) - min(ys) + 1) * cell_px)),
                ],
            )
        )
    return [b for _, b in sorted(out, key=lambda o: -o[0])]


def analyze(
    frames: Iterable[np.ndarray],
    times_ms: Sequence[float],
    *,
    cell: int = CELL,
    px: float = 1.0,
    fine: bool = True,
    mask: np.ndarray | None = None,
    origin: tuple[float, float] = (0.0, 0.0),
) -> Analysis:
    """Count flashes in `frames` (uint8 H x W x 3, one per time in
    `times_ms`). `px`: CSS px per frame pixel (a video drawn at a quarter of
    full screen has px 4, and cell 1 keeps cells 4 CSS px). `mask`: pixels
    left out (real-time media in a stepped capture). `origin`: where the
    frames' top left corner is, in CSS px, for the boxes reported."""
    times = np.asarray(times_ms, np.float64)
    cell_px = cell * px
    gen = red = red22 = pix = None
    series: list[np.ndarray] = []
    grid = (0, 0)
    n = 0
    for frame in frames:
        rgb = np.asarray(frame)[..., :3]
        if mask is not None:
            rgb = np.where(mask[..., None], 0, rgb).astype(np.uint8)
        lin = linear(rgb)
        cl = blocks(lin, cell)
        lum = luminance(cl)
        rv, ratio = red_values(cl)
        if gen is None:
            grid = lum.shape
            nc = lum.size
            gen = Hysteresis(nc, GENERAL_DELTA)
            red = Hysteresis(nc, RED_DELTA, strict=True)
            red22 = Hysteresis2D(nc)
        gen.step(lum)
        red.step(rv, ratio)
        red22.step(chromaticity(cl), ratio)
        if fine:
            pl = luminance(lin[::FINE_STRIDE, ::FINE_STRIDE])
            if pix is None:
                pix = Hysteresis(pl.size, GENERAL_DELTA)
                pgrid = pl.shape
            pix.step(pl)
        if n < SERIES_MAX:
            series.append(lum.astype(np.float16).ravel())
        n += 1
    out = Analysis(frames=n)
    if gen is None or n < 2:
        return out
    times = times[:n]
    out.span_ms = round(float(times[-1] - times[0]), 1)
    tg = gen.finish()
    ok_g = np.minimum(tg[3], tg[4]) < DARK_MAX
    out.general, flash_g = _kind(times, tg, ok_g, grid, cell_px, origin)
    tr = red.finish()
    ok_r = (tr[5] >= RED_RATIO) | (tr[6] >= RED_RATIO)
    out.red, flash_r = _kind(times, tr, ok_r, grid, cell_px, origin)
    t22 = red22.finish()
    ok_22 = (t22[5] >= RED_RATIO) | (t22[6] >= RED_RATIO)
    out.red22, _ = _kind(times, t22, ok_22, grid, cell_px, origin)
    flashing = np.union1d(flash_g, flash_r)
    gh, gw = grid
    if pix is not None:
        tp = pix.finish()
        okp = np.minimum(tp[3], tp[4]) < DARK_MAX
        pc, pcounts = window_counts(times, tp[7][okp], tp[0][okp], pix.n)
        hot = pc[(pcounts > MAX_TRANSITIONS).any(axis=0)] if len(pc) else pc
        if len(hot):
            ph, pw = pgrid
            py, pxx = hot // pw, hot % pw
            cy = (py * FINE_STRIDE) // cell
            cx = (pxx * FINE_STRIDE) // cell
            near = np.zeros((gh + 2, gw + 2), bool)
            if len(flashing):
                fy, fx = flashing // gw, flashing % gw
                for dy in (0, 1, 2):
                    for dx in (0, 1, 2):
                        near[fy + dy, fx + dx] = True
            alone = ~near[cy + 1, cx + 1]
            out.fine_pixels = int(alone.sum())
            out.fine = out.fine_pixels > 0
            if out.fine:
                flashing = np.union1d(flashing, np.unique(cy[alone] * gw + cx[alone]))
    out.boxes = _boxes(flashing, grid, cell_px, origin)
    if len(flashing) and series:
        counts = np.bincount(tg[0][ok_g], minlength=gh * gw)
        busiest = int(flashing[np.argmax(counts[flashing])])
        out.series = [round(float(s[busiest]), 3) for s in series]
        out.series_box = [
            int(round(origin[0] + (busiest % gw) * cell_px)),
            int(round(origin[1] + (busiest // gw) * cell_px)),
            int(round(cell_px)),
            int(round(cell_px)),
        ]
    return out


def steps_ms(seconds: float, fps: int = 60) -> list[int]:
    """Whole-millisecond clock steps for `seconds` at `fps` (60: 17, 16, 17,
    so every third step lands on an exact 1/60 s multiple)."""
    out, t = [], 0
    for k in range(1, round(seconds * fps) + 1):
        nxt = round(k * 1000 / fps)
        out.append(nxt - t)
        t = nxt
    return out


def resample(
    durations_ms: Sequence[float], loops: int, fps: int = 60
) -> tuple[list[int], list[float]]:
    """Frame indices shown at each 1/fps tick over `loops` plays of an
    animated image whose frames last `durations_ms`, and the tick times."""
    total = float(sum(durations_ms))
    if total <= 0:
        return [0], [0.0]
    edges = np.cumsum(durations_ms)
    n = int(total * loops * fps / 1000)
    ticks = np.arange(n) * 1000.0 / fps
    idx = np.searchsorted(edges, ticks % total, side="right")
    idx = np.minimum(idx, len(durations_ms) - 1)
    return [int(i) for i in idx], [float(t) for t in ticks]
