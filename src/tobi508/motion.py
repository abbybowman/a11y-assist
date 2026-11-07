"""Pass T: one fresh load of the recorded page, watched with no input
(2.C spec section 2; shared by 2.A, 2.B, 2.C and 2.D).

Records facts only: frames and the regions whose pixels changed, what each
region's content did (its text, image sources and rendered children at three
reads), DOM changes with their targets and the live region around each,
timers, Web Audio use, animations, media state per frame, dialogs, focus
moves with no key pressed, and polls in the HAR. Which test applies, and its
outcome, is each 2.x check's rules.

Pass T takes an opener (`OpenPage`): a fresh replay load with
`MOTION_INIT_JS` added before page scripts (plan Q7). Which browser that
load runs in is the pipeline's choice (plan Q1 and Q11), not this module's.

Verified behavior this module depends on (plan "Verified" items; tests in
tests/test_motion.py):
  * Pixel differences classify motion; DOM signals do not (item 6). Tiles
    map to elements by overlap, not by their centre.
  * Timer hooks run before page scripts and see periods longer than the
    watch (item 7).
  * The replay answers every repeat of a request with its first recorded
    response, so polling shows only in the HAR (item 10).
"""

from __future__ import annotations

import asyncio
import io
import json
import statistics
import time
import zipfile
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops
from playwright.async_api import BrowserContext, Frame, Page
from pydantic import BaseModel, Field

from tobi508.browser import AUTOPLAY_ARG, MOTION_BROWSER  # noqa: F401
from tobi508.observe import DIALOGS_JS
from tobi508.redact import safe_error
from tobi508.site import UNITS_FN
from tobi508.traverse import PATH_JS, screenshot

# TT: "more than 5 seconds" (2.B) and "more than 3 seconds" (2.A); the
# watch is 6.5 s at the top of the page (Abby, 2026-11-03, plan Q3).
WATCH_S = 6.5
# Frames alternate 0.35 s and 0.45 s apart (0.4 s on average): at a steady
# 0.5 s, a blink of 0.5 s per state was seen in the same state every frame.
FRAME_STEPS = (0.35, 0.45)
FRAME_S = sum(FRAME_STEPS) / len(FRAME_STEPS)
READS_AT = (0.0, 3.5, 6.5)
TILE = 20
# Bounds that keep one pass small on a busy page; reaching one is recorded.
MAX_COMPONENTS = 30  # changed-tile groups mapped per frame
MAX_REGIONS = 40
MAX_BOXES = 400  # changed-pixel boxes kept per region
FAST_KEPT = 300  # 3.A's fast callbacks kept per frame
# A frame where more than this share of the viewport's tiles changed is a
# page-wide change (a dialog's backdrop, a scroll), noted and not mapped.
PAGE_CHANGE = 0.5


OpenPage = Callable[[], Awaitable[tuple[BrowserContext, Page]]]

# ANDI 29.2.2's live regions (sandi.js): aria-live polite or assertive, and
# roles alert, status, log, marquee and timer (2.D spec, Terms). An element
# whose aria-live is anything else (off) is not one.
LIVE_SELECTOR = (
    "[aria-live],[role=alert],[role=status],[role=log],[role=marquee],[role=timer]"
)
# Carousel containers (2.C spec, Terms): the content is the whole carousel.
CAROUSEL_SELECTOR = (
    "[aria-roledescription~=carousel i],.slick-slider,.splide,.swiper,"
    ".carousel,.glide,.flickity-enabled"
)

# Runs in every frame before page scripts, after traverse.INIT_JS.
MOTION_INIT_JS = (
    (
        "(() => {"
        + PATH_JS
        + """
  if (window.__a11yMotion) return;
  const now = () => performance.timeOrigin + performance.now();
  const M = { recs: [], attrs: 0, dropped: 0, timers: [], audio: 0, snaps: [], live0: new WeakSet(), held: new Map(), focus: [], ctxs: new Set(), io: [], t0: null };
  Object.defineProperty(window, '__a11yMotion', { value: M });
  const REC_MAX = 1500, ATTR_MAX = 300, TIMER_MAX = 200;
  const LIVE = LIVE_SELECTOR;
  const CAROUSEL = CAROUSEL_SELECTOR;
  const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const isLive = (e) => {
    if (!e.matches(LIVE)) return false;
    if (!e.hasAttribute('aria-live')) return true;
    const v = norm(e.getAttribute('aria-live')).toLowerCase();
    return v === 'polite' || v === 'assertive';
  };
  const liveOf = (el) => { for (let e = el; e; e = e.parentElement) if (isLive(e)) return e; return null; };
  // 3.A's triggers (3.A spec section 2): callbacks of timers under 334 ms
  // and of requestAnimationFrame that change the page or draw on a canvas,
  // by time. A second observer's takeRecords() sees a callback's own DOM
  // changes synchronously, without taking them from the observer below.
  M.fast = []; M.draws = 0;
  const FAST_MS = 334, FAST_MAX = 600;
  const fx = new MutationObserver(() => {});
  fx.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
  const drawHook = (C, names) => {
    if (!C) return;
    for (const k of names) {
      const o = C.prototype[k];
      if (typeof o === 'function') C.prototype[k] = function (...a) { M.draws++; return o.apply(this, a); };
    }
  };
  const D2 = ['fillRect', 'clearRect', 'strokeRect', 'fill', 'stroke', 'drawImage', 'putImageData', 'fillText', 'strokeText'];
  drawHook(window.CanvasRenderingContext2D, D2);
  drawHook(window.OffscreenCanvasRenderingContext2D, D2);
  drawHook(window.WebGLRenderingContext, ['drawArrays', 'drawElements', 'clear']);
  drawHook(window.WebGL2RenderingContext, ['drawArrays', 'drawElements', 'clear']);
  const fast = (f, kind) => function (...a) {
    const d0 = M.draws;
    try { return f.apply(this, a); } finally {
      try { if ((fx.takeRecords().length || M.draws !== d0) && M.fast.length < FAST_MAX) M.fast.push({ at: now(), kind }); } catch (e) {}
    }
  };
  const raf = window.requestAnimationFrame;
  if (raf) window.requestAnimationFrame = function (f, ...a) { return raf.call(this, typeof f === 'function' ? fast(f, 'raf') : f, ...a); };
  // Timers (2.C A2: a period longer than the watch, item 7).
  const si = window.setInterval, st = window.setTimeout;
  window.setInterval = function (f, ms, ...a) {
    const v = Number(ms) || 0;
    if (v >= 1000 && M.timers.length < TIMER_MAX) M.timers.push({ kind: 'interval', ms: Math.round(v), at: now() });
    if (typeof f === 'function' && v < FAST_MS) f = fast(f, 'interval');
    return si.call(this, f, ms, ...a);
  };
  window.setTimeout = function (f, ms, ...a) {
    const v = Number(ms) || 0;
    if (v >= 1000 && M.timers.length < TIMER_MAX) M.timers.push({ kind: 'timeout', ms: Math.round(v), at: now() });
    if (typeof f === 'function' && v < FAST_MS) f = fast(f, 'timeout');
    return st.call(this, f, ms, ...a);
  };
  // What the page waits to see scrolled into view (Understanding 2.2.2:
  // starting when scrolled into view counts as starting by itself).
  if (window.IntersectionObserver) {
    const io = IntersectionObserver.prototype.observe;
    IntersectionObserver.prototype.observe = function (t) {
      try { if (t && t.nodeType === 1 && M.io.length < 50) M.io.push(t); } catch (e) {}
      return io.apply(this, arguments);
    };
  }
  // Web Audio connected to the speakers (2.A, item 5).
  if (window.AudioNode) {
    const cn = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function (d, ...a) {
      try { if (window.AudioDestinationNode && d instanceof AudioDestinationNode) { M.audio++; M.ctxs.add(d.context); } } catch (e) {}
      return cn.call(this, d, ...a);
    };
  }
  // DOM changes with their targets (2.D: the change, and the live region
  // around it at the time). The <head> is skipped: the tool's screenshots
  // add and remove a style element there.
  const textOf = (el) => norm(el && (el.innerText !== undefined ? el.innerText : el.textContent)).slice(0, 200);
  const meaningful = (nodes) => Array.from(nodes).some((n) => n.nodeType === 1 || (n.nodeType === 3 && norm(n.textContent)));
  const obs = new MutationObserver((rs) => {
    const at = now();
    for (const r of rs) {
      const el = r.target.nodeType === 1 ? r.target : r.target.parentElement;
      if (!el || (el.closest && el.closest('head'))) continue;
      let kind;
      if (r.type === 'characterData') kind = 'text';
      else if (r.type === 'childList') { if (!meaningful(r.addedNodes) && !meaningful(r.removedNodes)) continue; kind = 'children'; }
      else kind = ['src', 'srcset', 'poster'].includes(r.attributeName) ? 'src' : 'attr';
      if (kind === 'attr') { if (M.attrs >= ATTR_MAX) { M.dropped++; continue; } M.attrs++; }
      if (M.recs.length >= REC_MAX) { M.dropped++; continue; }
      M.recs.push({ at, kind, attr: r.attributeName || null, el, live: liveOf(el),
        before: r.type === 'characterData' ? norm(r.oldValue).slice(0, 200) : '',
        after: kind === 'text' || kind === 'children' ? textOf(el) : '' });
    }
  });
  obs.observe(document, { subtree: true, childList: true, attributes: true, characterData: true, characterDataOldValue: true });
  // Focus moves with no key pressed (2.D N4), as element references.
  addEventListener('focusin', (e) => { if (M.focus.length < 100) M.focus.push({ at: now(), el: e.composedPath()[0] }); }, true);
  // Pass T's start: live regions present and rendered now (2.D: a region
  // added with the change does not count).
  M.mark0 = () => {
    M.t0 = now();
    const vis = (e) => e.checkVisibility ? e.checkVisibility({ visibilityProperty: true }) : e.getClientRects().length > 0;
    const out = [];
    for (const e of document.querySelectorAll(LIVE)) {
      if (!isLive(e) || !vis(e)) continue;
      M.live0.add(e);
      out.push({ css: path(e), role: e.getAttribute('role') || '', live: norm(e.getAttribute('aria-live')) });
    }
    const car = Array.from(document.querySelectorAll(CAROUSEL)).slice(0, 10).map((e) => path(e));
    return { t0: M.t0, live: out, carousels: car };
  };
  // What each element shows (2.C Terms, kind): a hash of its visible text,
  // image sources and rendered children, and its box. Text clipped away by
  // an overflow ancestor (a sliding carousel's other slides) is not shown.
  const H = (h, s) => { for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0; return h; };
  M.snap = () => {
    const map = new WeakMap();
    const visit = (el, clip, faded) => {
      let cs;
      try { cs = getComputedStyle(el); } catch (e) { return 0; }
      if (cs.display === 'none') return 0;
      const r = el.getBoundingClientRect();
      const fade = faded || parseFloat(cs.opacity) === 0;
      let c = clip;
      if (cs.display !== 'contents' && (cs.overflowX !== 'visible' || cs.overflowY !== 'visible'))
        c = [Math.max(clip[0], r.left), Math.max(clip[1], r.top), Math.min(clip[2], r.right), Math.min(clip[3], r.bottom)];
      const inClip = r.width > 0 && r.height > 0 && r.right > clip[0] && r.left < clip[2] && r.bottom > clip[1] && r.top < clip[3];
      const self = !fade && cs.visibility !== 'hidden' && (inClip || cs.display === 'contents');
      let h = 2166136261, n = 0;
      // What it looks like apart from its content (2.B: a colour-only
      // change is blinking) and how it is placed (a spinner rotates).
      let ch = 2166136261, th = 2166136261;
      if (self) {
        ch = H(ch, [cs.color, cs.backgroundColor, cs.borderTopColor, cs.fill, cs.stroke, cs.opacity, cs.visibility].join('|'));
      }
      th = H(th, cs.transform + '|' + cs.translate + '|' + cs.rotate + '|' + cs.scale);
      if (self) {
        for (const t of el.childNodes) if (t.nodeType === 3) { const s = norm(t.textContent); if (s) { h = H(h, s); n++; } }
        if (el.tagName === 'IMG') { h = H(h, 'img:' + (el.currentSrc || el.src || '')); n++; }
        if (cs.backgroundImage && cs.backgroundImage !== 'none') { h = H(h, 'bg:' + cs.backgroundImage); n++; }
        if ((el.tagName === 'INPUT' && el.type !== 'hidden') || el.tagName === 'TEXTAREA') { h = H(h, 'v:' + el.value); n++; }
      }
      const kids = el.shadowRoot ? [...el.shadowRoot.children, ...el.children] : el.children;
      for (const k of kids) {
        const hk = visit(k, c, fade);
        if (hk) { h = H(h, String(hk)); n++; }
        const v = map.get(k);
        if (v) { ch = H(ch, String(v[5])); th = H(th, String(v[6])); }
      }
      const out = n ? h >>> 0 : 0;
      map.set(el, [out, Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height), ch >>> 0, th >>> 0]);
      return out;
    };
    const t = now();
    if (document.body) visit(document.body, [-1e9, -1e9, 1e9, 1e9], false);
    M.snaps.push({ at: t, map });
    return t;
  };
  // Regions for a group of changed tiles (2.C Terms, region). `boxes` are
  // the changed pixels' bounding boxes, one per tile, in viewport pixels.
  // The group goes to the smallest element whose box covers it, by overlap
  // (not by tile centres, which missed edge tiles; item 6). When its
  // changed pixels fall in two or more of that element's children, one in
  // each, each child's part is its own region (two widgets side by side).
  // Inside a carousel, the region is the whole carousel. An iframe hands its
  // part to its own frame.
  const ov = (r, b) => Math.max(0, Math.min(r.right, b[2]) - Math.max(r.left, b[0])) * Math.max(0, Math.min(r.bottom, b[3]) - Math.max(r.top, b[1]));
  // 4 px of slack: a focus ring is drawn just outside its element.
  const covers = (r, b) => r.left <= b[0] + 4 && r.top <= b[1] + 4 && r.right >= b[2] - 4 && r.bottom >= b[3] - 4;
  // Covering now and at the first read: content that moved there (the slide
  // in view at the end of a sliding carousel) does not cover it.
  const steady = (e, b) => {
    if (!covers(e.getBoundingClientRect(), b)) return false;
    const v = M.snaps.length ? M.snaps[0].map.get(e) : null;
    return !v || covers({ left: v[1], top: v[2], right: v[1] + v[3], bottom: v[2] + v[4] }, b);
  };
  const bboxOf = (bs) => [Math.min(...bs.map((b) => b[0])), Math.min(...bs.map((b) => b[1])), Math.max(...bs.map((b) => b[2])), Math.max(...bs.map((b) => b[3]))];
  const rendered = (e) => { try { return getComputedStyle(e).display !== 'none'; } catch (x) { return false; } };
  const cover = (bs) => {
    const bx = bboxOf(bs), seen = new Set();
    const step = Math.max(1, Math.floor(bs.length / 24));
    for (let i = 0; i < bs.length; i += step) {
      const b = bs[i];
      for (const e of document.elementsFromPoint((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)) seen.add(e);
    }
    let best = null, area = Infinity, over = null, most = 0, overArea = Infinity;
    for (const e of seen) {
      const r = e.getBoundingClientRect(), a = r.width * r.height;
      if (steady(e, bx)) { if (a < area) { area = a; best = e; } }
      else { const o = ov(r, bx); if (o > most || (o === most && a < overArea)) { most = o; over = e; overArea = a; } }
    }
    return { el: best || over || document.body, covered: !!best };
  };
  const split = (el, idx, bs, depth) => {
    if (depth > 12 || idx.length < 2 || el.tagName === 'IFRAME' || el.tagName === 'FRAME') return [[el, idx]];
    const kids = (el.shadowRoot ? [...el.shadowRoot.children, ...el.children] : Array.from(el.children))
      .filter(rendered).map((c) => [c, c.getBoundingClientRect()]);
    const parts = new Map();
    for (const i of idx) {
      const hit = kids.filter(([, r]) => ov(r, bs[i]) > 0);
      if (hit.length !== 1) return [[el, idx]];
      const c = hit[0][0];
      if (!parts.has(c)) parts.set(c, []);
      parts.get(c).push(i);
    }
    if (parts.size < 2) return [[el, idx]];
    const out = [];
    for (const [c, sub] of parts) {
      // The smallest descendant of c covering its part.
      let e = c;
      const bx = bboxOf(sub.map((i) => bs[i]));
      for (let k = 0; k < 30; k++) {
        const next = Array.from(e.children).filter(rendered).find((d) => steady(d, bx));
        if (!next) break;
        e = next;
      }
      out.push(...split(e, sub, bs, depth + 1));
    }
    return out;
  };
  M.regionsAt = (bs) => {
    if (!bs.length) return [];
    const all = bs.map((_, i) => i);
    let { el: top, covered } = cover(bs);
    // A running animation's target whose box, grown by half its size (a
    // rotated square reaches about 0.21 of its side past its box), covers the
    // changed pixels is the region: a spinning badge, not the <main> around
    // it, whose other content never changed.
    const bx = bboxOf(bs);
    let best = null, area = Infinity;
    for (const a of document.getAnimations()) {
      const t = a.effect && a.effect.target;
      if (!t || t.nodeType !== 1 || a.playState !== 'running' || !(top === t || top.contains(t))) continue;
      const r = t.getBoundingClientRect(), g = Math.max(r.width, r.height) / 2;
      const grown = { left: r.left - g, top: r.top - g, right: r.right + g, bottom: r.bottom + g };
      if (covers(grown, bx) && r.width * r.height < area) { best = t; area = r.width * r.height; }
    }
    if (best) { top = best; covered = true; }
    const frames = Array.from(document.querySelectorAll('iframe, frame'));
    return split(top, all, bs, 0).map(([el0, idx]) => {
      if (el0.tagName === 'IFRAME' || el0.tagName === 'FRAME') {
        const r = el0.getBoundingClientRect();
        return { frame: frames.indexOf(el0), dx: r.left + el0.clientLeft, dy: r.top + el0.clientTop, idx };
      }
      const car = el0.closest(CAROUSEL);
      let el = car || el0;
      // An element that was not on the page at the first read (replaced
      // with innerHTML every second): its region is the ancestor that was.
      const first = M.snaps.length ? M.snaps[0].map : null;
      while (first && !first.has(el) && el.parentElement && el !== document.body) el = el.parentElement;
      const css = path(el);
      M.held.set(css, el);
      const r = el.getBoundingClientRect();
      return { css, tag: el.tagName.toLowerCase(), part: el !== el0 ? path(el0) : null, carousel: !!car, covered, idx,
        box: [Math.round(r.left + scrollX), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)] };
    });
  };
  // A region at the end of the watch: what it showed at each read, whether
  // its children moved, its DOM changes and their live regions.
  M.describe = (css) => {
    const el = M.held.get(css);
    if (!el) return null;
    const sigs = M.snaps.map((s) => { const v = s.map.get(el); return v ? v[0] : null; });
    const colors = M.snaps.map((s) => { const v = s.map.get(el); return v ? v[5] : null; });
    const transforms = M.snaps.map((s) => { const v = s.map.get(el); return v ? v[6] : null; });
    let moved = false;
    // Any descendant (capped), not only children: a sliding carousel's track
    // sits inside a clipping box. More than 20 px against the region: a
    // ticker gaining a digit nudges the inline text after it, which is not
    // motion.
    const kids = Array.from(el.querySelectorAll('*')).slice(0, 400);
    for (let i = 1; i < M.snaps.length && !moved; i++) {
      const a = M.snaps[i - 1].map, b = M.snaps[i].map, pa = a.get(el), pb = b.get(el);
      if (!pa || !pb) continue;
      for (const k of kids) {
        const ka = a.get(k), kb = b.get(k);
        if (ka && kb && ka[0] && (Math.abs((ka[1] - pa[1]) - (kb[1] - pb[1])) > 20 || Math.abs((ka[2] - pa[2]) - (kb[2] - pb[2])) > 20)) { moved = true; break; }
      }
    }
    const rec = (r) => ({ at: r.at, kind: r.kind, attr: r.attr, css: r.el.isConnected ? path(r.el) : '', before: r.before, after: r.after,
        live: r.live ? (r.live.isConnected ? path(r.live) : '') : null, live_at_start: !!(r.live && M.live0.has(r.live)) });
    const mine = M.recs.filter((r) => r.at >= M.t0 && (el === r.el || el.contains(r.el)));
    const changes = mine.filter((r) => r.kind !== 'attr').slice(0, 100).map(rec);
    // 2.D's note: inside or holding aria-live="off" (W3C's carousel pattern
    // turns announcements off while it rotates).
    const liveOff = !!(el.closest('[aria-live="off" i]') || el.querySelector('[aria-live="off" i]'));
    // Class and style changes (slides shown by a class or slid by transform): 2.D's changes when
    // a region shows new content with no text change.
    // Style changes too: a carousel that slides with transform has nothing else.
    const attrList = mine.filter((r) => r.kind === 'attr').slice(0, 30).map(rec);
    const attrs = mine.filter((r) => r.kind === 'attr').length;
    const focusIn = M.focus.filter((f) => f.at >= M.t0 && (el === f.el || el.contains(f.el))).map((f) => f.at);
    let anims = [];
    try {
      anims = el.getAnimations({ subtree: true }).slice(0, 20).map((a) => {
        const t = a.effect ? a.effect.getComputedTiming() : {};
        const target = a.effect && a.effect.target;
        return { css: target && target.nodeType === 1 ? path(target) : '', name: a.animationName || a.transitionProperty || a.id || '',
          infinite: t.iterations === Infinity, iterations: t.iterations === Infinity ? 0 : (t.iterations || 0),
          duration_ms: typeof t.duration === 'number' ? Math.round(t.duration) : 0, state: a.playState };
      });
    } catch (e) {}
    return { live_off: liveOff, sigs, colors, transforms, moved, changes, attr_list: attrList, attrs, focus_in: focusIn, anims, text: textOf(el), connected: el.isConnected };
  };
  M.media = () => Array.from(document.querySelectorAll('video, audio')).slice(0, 20).map((m) => ({
    css: path(m), tag: m.tagName.toLowerCase(), paused: m.paused, muted: m.muted, volume: m.volume,
    time: m.currentTime, duration: isFinite(m.duration) ? m.duration : null, loop: m.loop, autoplay: m.autoplay,
    controls: m.controls, error: m.error ? m.error.code : null,
    decoded: typeof m.webkitAudioDecodedByteCount === 'number' ? m.webkitAudioDecodedByteCount : null,
    src: (m.currentSrc || '').slice(0, 500) }));
  // <blink> and text-decoration: blink do not blink in Chrome (plan item 9):
  // a note for 2.B only.
  const blinkMarkup = () => {
    if (document.querySelector('blink')) return true;
    const all = document.querySelectorAll('body *');
    for (let i = 0; i < all.length && i < 3000; i++) {
      if ((getComputedStyle(all[i]).textDecorationLine || '').includes('blink')) return true;
    }
    return false;
  };
  // 3.A's trigger: running animations whose colour, background (a pattern
  // shifted by its position), opacity, visibility or filter changes more
  // than 3 times a second (keyframe changes, each
  // steps(n) easing counting n, per iteration).
  const FLASHY = /^(color|background(Color|Image|Position|PositionX|PositionY|Size)?|opacity|visibility|filter|fill|stroke|border(Top|Right|Bottom|Left)?Color|outlineColor|boxShadow|textShadow)$/;
  M.fastAnims = () => {
    const out = [];
    for (const a of document.getAnimations()) {
      if (out.length >= 20) break;
      try {
        if (a.playState !== 'running' || !a.effect || !a.effect.getKeyframes) continue;
        const t = a.effect.getComputedTiming();
        const dur = typeof t.duration === 'number' ? t.duration : 0;
        if (!(dur > 0)) continue;
        const kf = a.effect.getKeyframes();
        const look = (k) => Object.keys(k).filter((p) => FLASHY.test(p)).map((p) => p + ':' + k[p]).sort().join('|');
        let changes = 0;
        for (let i = 1; i < kf.length; i++) {
          if (look(kf[i]) === look(kf[i - 1])) continue;
          const m = /steps\\((\\d+)/.exec(kf[i - 1].easing || '');
          changes += m ? Number(m[1]) : 1;
        }
        if (kf.length > 1 && look(kf[kf.length - 1]) !== look(kf[0]) && !String(t.direction || '').includes('alternate')) changes++;
        const perS = changes * 1000 / dur * Math.abs(a.playbackRate || 1);
        if (perS <= 3) continue;
        const tg = a.effect.target;
        out.push({ css: tg && tg.nodeType === 1 ? path(tg) : '', name: a.animationName || a.transitionProperty || a.id || '',
          per_s: Math.round(perS * 100) / 100, duration_ms: Math.round(dur) });
      } catch (e) {}
    }
    return out;
  };
  M.facts = () => ({ timers: M.timers, audio: M.audio, dropped: M.dropped, blink: blinkMarkup(),
    fast: M.fast.map((f) => ({ at: f.at, kind: f.kind })), fast_anims: M.fastAnims(),
    // Web Audio contexts playing to the speakers (2.A), and the iframes'
    // sources (2.A: a YouTube or Vimeo player cannot be measured).
    audio_states: Array.from(M.ctxs).map((c) => c.state),
    iframes: Array.from(document.querySelectorAll('iframe')).map((f) => (f.src || '').slice(0, 500)).slice(0, 30) });
  // Motion the frames may not show (below the first screen): animations
  // running with more than 5 s of active time, marquees, playing videos,
  // that are not inside a region already found (2.B Terms).
  // Hints below the first screen (2.C spec section 2, scrolled watch; plan
  // Q3): what the page observes for scrolling into view, and carousels,
  // that lie below the first viewport and are not inside a region found.
  M.below = (known) => {
    const inside = (e) => known.some((css) => { const r = M.held.get(css); return r && (r === e || r.contains(e)); });
    const out = [];
    const cand = [...M.io, ...document.querySelectorAll(CAROUSEL)];
    for (const e of cand) {
      if (!e.isConnected || inside(e)) continue;
      const r = e.getBoundingClientRect();
      if (r.top + scrollY < innerHeight || r.width === 0 || r.height === 0) continue;
      const css = path(e);
      if (!out.includes(css)) out.push(css);
    }
    return out.slice(0, 10);
  };
  M.images = () => Array.from(new Set(Array.from(document.images)
    .map((i) => (i.currentSrc || '').split('#')[0]).filter((u) => /^https?:/.test(u)))).slice(0, 30);
  M.extras = (known, longImages) => {
    const inside = (e) => known.some((css) => { const r = M.held.get(css); return r && (r === e || r.contains(e)); });
    const out = [];
    const add = (e, source, detail) => {
      if (!e || e.nodeType !== 1 || inside(e) || out.length >= 10) return;
      const css = path(e);
      if (out.some((o) => o.css === css)) return;
      M.held.set(css, e);
      known.push(css);
      const r = e.getBoundingClientRect();
      out.push({ css, tag: e.tagName.toLowerCase(), source, detail,
        box: [Math.round(r.left + scrollX), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)] });
    };
    for (const a of document.getAnimations()) {
      if (a.playState !== 'running' || !a.effect) continue;
      const t = a.effect.getComputedTiming();
      const active = t.iterations === Infinity ? Infinity : (t.iterations || 0) * (typeof t.duration === 'number' ? t.duration : 0);
      if (active > 5000) add(a.effect.target, 'animation', (a.animationName || a.transitionProperty || '') + (active === Infinity ? ' (infinite)' : ' ' + Math.round(active) + ' ms'));
    }
    for (const m of document.querySelectorAll('marquee')) add(m, 'marquee', 'marquee');
    // Animated images over 5 s in all, by G152 (frames x delays x loops,
    // decoded from the recording in the tool page), wherever they are.
    for (const i of document.images) {
      const d = (longImages || {})[(i.currentSrc || '').split('#')[0]];
      if (d) add(i, 'image', d);
    }
    // Content the DOM log saw keep changing where no frame showed it (below
    // the first screen): three or more text or child changes, the last at
    // 5 s or later.
    // Only changes that change its text: a poll that writes the same value
    // again (a replay answers every poll alike) is not an update.
    const byEl = new Map();
    for (const r of M.recs) {
      if (r.kind === 'attr' || r.at < M.t0 || !r.el || !r.el.isConnected) continue;
      const v = byEl.get(r.el) || { n: 0, last: 0, text: null };
      if (r.after !== v.text) {
        if (v.text !== null) { v.n++; v.last = Math.max(v.last, r.at); }
        v.text = r.after;
      }
      byEl.set(r.el, v);
    }
    for (const [e, v] of byEl) {
      if (v.n >= 3 && v.last - M.t0 >= 5000) add(e, 'dom', v.n + ' changes');
    }
    for (const v of document.querySelectorAll('video')) {
      if (!v.paused && (v.loop || (isFinite(v.duration) && v.duration - v.currentTime > 5))) add(v, 'video', v.loop ? 'playing, looping' : 'playing');
    }
    return out;
  };
  // The elements (read at 0 s, ELEMENTS_JS) inside a region's element.
  M.inside = (css) => {
    const el = M.held.get(css);
    if (!el || !M.els) return { inside: [], next: null };
    const out = [];
    M.els.forEach((e, i) => { if (el === e || el.contains(e)) out.push(i); });
    // Content with no element inside it (an empty spinning box) is placed
    // by document order: the first element that follows it.
    let next = null;
    if (!out.length) {
      next = M.els.findIndex((e) => el.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING);
      if (next < 0) next = M.els.length;
    }
    return { inside: out, next };
  };
})()"""
    )
    .replace("LIVE_SELECTOR", json.dumps(LIVE_SELECTOR))
    .replace("CAROUSEL_SELECTOR", json.dumps(CAROUSEL_SELECTOR))
)


# Elements (2.C Terms; Abby, 2026-11-03, plan Q6): what a screen reader reads
# as one unit, in reading order. site.UNITS_FN's units (as 9.A-9.C and 19.A
# read them), with three rules of its own: a label on the same line as its
# control is one element with it, content inside aria-hidden="true" is not an
# element, and an iframe's content is read in its own frame and counted at
# the iframe's place (pass_t splices it in). Images without alt text are
# already skipped by UNITS_FN; each table cell's own text is its own unit.
ELEMENTS_CAP = 600
ELEMENTS_JS = (
    "(cap) => {"
    + UNITS_FN
    + r"""
  const r = units(cap);
  const drop = new Set();
  r.els.forEach((el, i) => {
    if (r.units[i].kind !== 'control' || !el.labels) return;
    for (const lab of el.labels) {
      const j = r.els.findIndex((e, k) => k !== i && r.units[k].kind === 'text' && (e === lab || lab.contains(e)));
      if (j < 0) continue;
      const a = lab.getBoundingClientRect(), b = el.getBoundingClientRect();
      const shared = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (shared >= Math.min(a.height, b.height) / 2) drop.add(j);
    }
  });
  const keep = [], out = [];
  r.els.forEach((el, i) => {
    if (drop.has(i) || el.closest('[aria-hidden="true"]')) return;
    const u = r.units[i];
    keep.push(el);
    out.push({ kind: u.kind, role: u.role, name: (u.name || '').slice(0, 200), css: u.css, box: u.box, stop: !!u.stop,
      href: u.href_attr === undefined ? null : u.href_attr });
  });
  // A media element's own controls (V1): one control element, at its place
  // in document order; the walk focuses its play button inside it.
  for (const m of document.querySelectorAll('audio[controls], video[controls]')) {
    if (!shown(m) || m.closest('[aria-hidden="true"]')) continue;
    let at = keep.findIndex((e) => m.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING);
    if (at < 0) at = keep.length;
    const b = m.getBoundingClientRect();
    keep.splice(at, 0, m);
    out.splice(at, 0, { kind: 'control', role: m.tagName.toLowerCase(), name: 'media controls', css: path(m),
      box: [Math.round(b.x + scrollX), Math.round(b.y + scrollY), Math.round(b.width), Math.round(b.height)],
      stop: true, href: null });
  }
  if (window.__a11yMotion) window.__a11yMotion.els = keep;
  return { elements: out, truncated: r.truncated };
}"""
)


class Element(BaseModel):
    i: int  # position in reading order, iframe content inline
    frame: int  # index in page.frames
    kind: str  # text | heading | image | control
    role: str = ""
    name: str = ""
    css: str
    box: list[int] = Field(default_factory=list)  # page x, y, width, height
    stop: bool = False  # natively tabbable or tabindex >= 0
    href: str | None = None  # a link's href attribute as written
    frame_url: str = ""  # "" in the top page


async def read_elements(page: Page) -> tuple[list[Element], bool, dict]:
    """Elements of every frame, inline at each iframe's place. Returns the
    elements, whether a cap cut them short, and (frame index, local index)
    -> element index, for `inside`."""
    out: list[Element] = []
    where: dict[tuple[int, int], int] = {}
    truncated = False

    async def visit(frame: Frame, depth: int) -> None:
        nonlocal truncated
        try:
            got = await frame.evaluate(ELEMENTS_JS, ELEMENTS_CAP)
        except Exception:
            truncated = True
            return
        truncated = truncated or got["truncated"]
        index = page.frames.index(frame) if frame in page.frames else -1
        for j, u in enumerate(got["elements"]):
            if u["kind"] == "frame":
                child = None
                if depth < 3:
                    try:
                        h = await frame.query_selector(u["css"])
                        child = await h.content_frame() if h else None
                    except Exception:
                        child = None
                if child is not None:
                    await visit(child, depth + 1)
                else:
                    truncated = True  # a frame not read: its content is missing
                continue
            if len(out) >= ELEMENTS_CAP:
                truncated = True
                return
            where[(index, j)] = len(out)
            out.append(
                Element(
                    i=len(out), frame=index, frame_url=frame.url if index else "", **u
                )
            )

    await visit(page.main_frame, 0)
    return out, truncated, where


class Change(BaseModel):
    """One DOM change inside a region during the watch (2.D spec, Terms)."""

    t: float  # seconds from the start of the watch
    kind: str  # text | children | src
    attr: str | None = None
    css: str = ""  # the changed element ("" once it left the page)
    before: str = ""
    after: str = ""
    live: str | None = None  # the live region around it when it changed
    live_at_start: bool = False  # that live region was there at 0 s


class Animation(BaseModel):
    css: str = ""
    name: str = ""
    infinite: bool = False
    iterations: float = 0
    duration_ms: int = 0
    state: str = ""


class Region(BaseModel):
    """Tiles that changed together, mapped to the smallest element covering
    them (2.C spec, Terms). `kinds` follows the Terms: "updating" when what
    it shows changed between reads, "moving" when its pixels changed but
    what it shows did not, or its children moved."""

    key: str  # "<frame>|<css>"
    frame: int  # index in page.frames (0: the top page)
    frame_url: str = ""
    css: str
    tag: str = ""
    content_css: str  # what the mechanism windows are counted around
    carousel: bool = False  # the region is a carousel (2.C Terms)
    parts: list[str] = Field(default_factory=list)  # elements merged into it
    covered: bool = True  # an element covered every changed tile
    box: list[int] = Field(default_factory=list)  # page x, y, width, height
    changed_at: list[float] = Field(default_factory=list)  # frame times
    tiles: int = 0
    sigs: list[int | None] = Field(default_factory=list)  # per read
    colors: list[int | None] = Field(default_factory=list)  # per read (2.B)
    transforms: list[int | None] = Field(default_factory=list)  # per read
    states: int = 0  # distinct looks of its box over the frames (top page; capped)
    # pixels (changed in the frames), or what showed motion the frames could
    # not: animation (over 5 s of active time), marquee or video (2.B Terms),
    # or dom: content the DOM log saw keep changing off screen (2.C)
    source: str = "pixels"
    source_detail: str = ""
    updated: bool = False
    children_moved: bool = False
    kinds: list[str] = Field(default_factory=list)
    text: str = ""  # its text at the end, capped
    connected: bool = True
    changes: list[Change] = Field(default_factory=list)
    attr_changes: int = 0
    attr_list: list[Change] = Field(default_factory=list)  # class and other attributes
    focus_in: list[float] = Field(default_factory=list)  # focus moved into it, s
    animations: list[Animation] = Field(default_factory=list)
    period_s: float | None = None  # median time between pixel changes
    scrolled: bool = False  # found by the scrolled watch (plan Q3)
    live_off: bool = False  # inside or holding aria-live="off" (2.D note)
    elements: list[int] = Field(default_factory=list)  # Element.i inside it
    # With no element inside: the first element after it in reading order
    # (len(elements) when none follows), so its windows can still be counted.
    next_element: int | None = None
    # Its changed pixels over the watch, one box per 20 px tile (x0, y0, x1,
    # y1 in the top page's viewport), capped: which elements really changed.
    changed_boxes: list[list[int]] = Field(default_factory=list)
    # Two pictures cut around it, about CROP_GAP_S apart (run-folder paths),
    # when no frame shows it whole: below the first screen, or found by the
    # scrolled watch (2.B 1.1.0; judge eval run 16).
    crops: list[str] = Field(default_factory=list)


class LiveRegion(BaseModel):
    frame: int
    css: str
    role: str = ""
    live: str = ""


class Timer(BaseModel):
    frame: int
    kind: str  # interval | timeout
    ms: int
    count: int = 1


class Media(BaseModel):
    frame: int
    frame_url: str = ""  # "" in the top page; the probe finds the frame by it
    at: float  # read time, seconds from the start of the watch
    css: str
    tag: str
    paused: bool
    muted: bool
    volume: float
    time: float
    duration: float | None = None
    loop: bool = False
    autoplay: bool = False
    controls: bool = False
    error: int | None = None
    decoded: int | None = None
    src: str = ""


class Poll(BaseModel):
    """Requests repeated to one address: in the HAR, or made during pass T
    (item 10: the replay answers every repeat with the first response, so
    the page cannot show new data). Recording stops once the network is
    idle, so a page polling every second may show only once in the HAR."""

    url: str
    count: int
    gap_ms: int | None = None  # median gap between repeats
    source: str = "har"  # har (while recording) | watch (requests in pass T)


class FocusMove(BaseModel):
    t: float
    css: str | None = None
    type: str = "focusin"


class Dialog(BaseModel):
    css: str
    name: str = ""
    role: str = ""
    text: str = ""
    keyboard: bool = False  # focus is in it, or it holds a focusable element


_DIALOG_FACTS_JS = """(css) => {
  const d = document.querySelector(css);
  if (!d) return null;
  const f = 'a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex^="-"])';
  return { role: d.getAttribute('role') || (d.tagName === 'DIALOG' ? 'dialog' : ''),
    text: (d.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 300),
    keyboard: d.contains(document.activeElement) || !!d.querySelector(f) };
}"""


class MotionPass(BaseModel):
    ok: bool = True
    error: str = ""
    watch_s: float = WATCH_S
    browser: str = ""  # the browser that ran pass T (browser.MOTION_BROWSER)
    frames: list[float] = Field(default_factory=list)  # times of each frame
    shots: list[str] = Field(default_factory=list)  # run-folder paths
    reads: list[float] = Field(default_factory=list)  # times of the reads
    viewport: list[int] = Field(default_factory=list)  # width, height
    regions: list[Region] = Field(default_factory=list)
    regions_capped: bool = False
    page_changes: list[float] = Field(default_factory=list)  # most of it changed
    unmapped_tiles: int = 0  # changed tiles with no element (a frame not read)
    live_regions: list[LiveRegion] = Field(default_factory=list)  # at 0 s
    dialogs_at_start: list[str] = Field(default_factory=list)
    dialogs_opened: list[Dialog] = Field(default_factory=list)
    focus_moves: list[FocusMove] = Field(default_factory=list)
    timers: list[Timer] = Field(default_factory=list)
    audio_connects: int = 0
    media: list[Media] = Field(default_factory=list)
    polls: list[Poll] = Field(default_factory=list)
    carousels: list[str] = Field(default_factory=list)  # "<frame>|<css>" at 0 s
    blink_markup: bool = False  # <blink> or text-decoration: blink (2.B note)
    # Below the first screen, not in a region (plan Q3): observed for
    # scrolling into view, or carousels. The scrolled watch looks at the first.
    below: list[str] = Field(default_factory=list)
    # Walk steps whose DOM never settled (2.C A2's walk cross-check), set by
    # the checks from ctx.cache["walk_unsettled"] once the walk has run.
    walk_unsettled: int = 0
    scrolled_watch: str | None = None  # what the scrolled watch scrolled to
    # G152: each animated image's frames, one play-through, loops (-1:
    # forever) and total (None: forever), decoded from the recording.
    animated_images: list[dict[str, Any]] = Field(default_factory=list)
    audio_states: list[str] = Field(default_factory=list)  # Web Audio contexts
    iframes: list[str] = Field(default_factory=list)  # iframe sources, every frame
    # Peak level of each media source's recorded bytes, in dBFS, decoded in a
    # tool page (never the tested page); None when it could not be decoded.
    loudness: dict[str, float | None] = Field(default_factory=dict)
    # The media store's index from the recording (capture.media_index):
    # url, size, type, file (None when not stored) and over_cap.
    media_store: list[dict[str, Any]] = Field(default_factory=list)
    dropped_changes: int = 0
    frames_read: int = 0  # document frames read (the top page included)
    elements: list[Element] = Field(default_factory=list)  # at 0 s
    elements_truncated: bool = False
    # 3.A's triggers (3.A spec section 2): callbacks of timers under 334 ms
    # and of requestAnimationFrame that changed the page or drew on a canvas
    # (frame, t in s from the start of the watch, kind), capped; and running
    # animations whose colour, opacity, visibility or filter changes more
    # than 3 times a second.
    fast_callbacks: list[dict[str, Any]] = Field(default_factory=list)
    fast_animations: list[dict[str, Any]] = Field(default_factory=list)


def changed_tiles(
    a: Image.Image, b: Image.Image, tile: int = TILE
) -> dict[tuple[int, int], list[int]]:
    """(column, row) of every tile with any pixel different between frames,
    with the bounding box of its changed pixels (x0, y0, x1, y1, viewport
    pixels)."""
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
    if diff.getbbox() is None:
        return {}
    w, h = diff.size
    cols, rows = -(-w // tile), -(-h // tile)
    # Pad to whole tiles, then a box reduce: any changed pixel makes the
    # tile's mean non-zero.
    padded = Image.new("L", (cols * tile, rows * tile))
    padded.paste(diff, (0, 0))
    px = padded.reduce(tile).load()
    out: dict[tuple[int, int], list[int]] = {}
    for y in range(rows):
        for x in range(cols):
            if px[x, y]:
                x0, y0 = x * tile, y * tile
                bb = padded.crop((x0, y0, x0 + tile, y0 + tile)).getbbox()
                if bb:
                    out[(x, y)] = [x0 + bb[0], y0 + bb[1], x0 + bb[2], y0 + bb[3]]
    return out


def components(tiles: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    """Tiles that touch one another (8 neighbours), largest first."""
    left, out = set(tiles), []
    while left:
        start = left.pop()
        group, todo = {start}, [start]
        while todo:
            x, y = todo.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in left:
                        left.remove(n)
                        group.add(n)
                        todo.append(n)
        out.append(group)
    return sorted(out, key=len, reverse=True)


def polls_in_har(har: Path) -> list[Poll]:
    """GET requests repeated to one address, media and byte ranges excluded
    (a video fetched in ranges is not polling)."""
    try:
        with zipfile.ZipFile(har) as z:
            name = next(n for n in z.namelist() if n.endswith(".har"))
            entries = json.loads(z.read(name))["log"]["entries"]
    except Exception:
        return []
    seen: dict[str, list[str]] = {}
    for e in entries:
        req, res = e.get("request", {}), e.get("response", {})
        if req.get("method") != "GET":
            continue
        headers = {h.get("name", "").lower() for h in req.get("headers", [])}
        if "range" in headers:
            continue
        mime = (res.get("content", {}).get("mimeType") or "").lower()
        if mime.startswith(("image/", "font/", "video/", "audio/", "text/css")):
            continue
        seen.setdefault(req.get("url", ""), []).append(e.get("startedDateTime", ""))
    out = []
    for url, times in seen.items():
        if len(times) < 2 or not url:
            continue
        gap = None
        try:
            ts = sorted(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times)
            gaps = [(b - a).total_seconds() * 1000 for a, b in zip(ts, ts[1:])]
            gap = round(statistics.median(gaps)) if gaps else None
        except ValueError:
            pass
        out.append(Poll(url=url[:500], count=len(times), gap_ms=gap))
    return sorted(out, key=lambda p: -p.count)[:20]


async def _each_frame(page: Page, js: str, *args: Any) -> list[tuple[int, Frame, Any]]:
    out = []
    for i, frame in enumerate(page.frames):
        try:
            out.append((i, frame, await frame.evaluate(js, *args)))
        except Exception:
            continue
    return out


async def _map(frame: Frame, boxes: list[list[int]], depth: int = 0):
    """Regions for one tile group: a list of (Frame, info), where info["idx"]
    lists the group's boxes in that region. Follows iframes."""
    try:
        got = await frame.evaluate(
            "(b) => window.__a11yMotion ? window.__a11yMotion.regionsAt(b) : null",
            boxes,
        )
    except Exception:
        return []
    out = []
    for item in got or []:
        if "frame" not in item:
            out.append((frame, item))
            continue
        if depth >= 3:
            continue
        try:
            handles = await frame.query_selector_all("iframe, frame")
            child = await handles[item["frame"]].content_frame()
        except Exception:
            child = None
        if child is None:
            continue
        dx, dy = item["dx"], item["dy"]
        sub = [boxes[i] for i in item["idx"]]
        moved = [[b[0] - dx, b[1] - dy, b[2] - dx, b[3] - dy] for b in sub]
        for f, info in await _map(child, moved, depth + 1):
            info["idx"] = [item["idx"][i] for i in info["idx"]]
            out.append((f, info))
    return out


def _kinds(r: Region) -> list[str]:
    seen = [s for s in r.sigs]
    updated = len({s for s in seen if s is not None}) > 1 or (
        any(s is None for s in seen) and any(s is not None for s in seen)
    )
    r.updated = updated or any(c.kind in ("text", "children", "src") for c in r.changes)
    kinds = []
    if r.updated:
        kinds.append("updating")
    if (not r.updated and r.changed_at) or r.children_moved:
        kinds.append("moving")
    return kinds


async def pass_t(
    open_page: OpenPage,
    har: Path | None = None,
    shots: Path | None = None,
    rel: Path | None = None,
    watch_s: float = WATCH_S,
    scroll_to: str | None = None,
    prefix: str = "2t",
) -> MotionPass:
    """Watch one fresh load for `watch_s` with no input. Never raises: a load
    or read that fails gives `ok=False` with the reason (2.C A1).
    `scroll_to`: the scrolled watch (plan Q3), with that element scrolled
    into view first; `prefix` names its frames."""
    out = MotionPass(watch_s=watch_s)
    if har is not None:
        out.polls = polls_in_har(har)
    try:
        context, page = await open_page()
    except Exception as exc:
        out.ok, out.error = False, f"the page could not be loaded: {safe_error(exc)}"
        return out
    try:
        if scroll_to:
            await page.evaluate(
                "(css) => { const e = document.querySelector(css); "
                "if (e) e.scrollIntoView({ block: 'center' }); }",
                scroll_to,
            )
            await page.wait_for_timeout(300)
        await _watch(page, out, shots, rel, watch_s, har, prefix)
        if shots is not None:
            try:
                await _crops(page, out, shots, rel, prefix, every=bool(scroll_to))
            except Exception:
                pass  # evidence for a question only; the frames still stand
        if har is not None:
            from tobi508.capture import media_index

            out.media_store = media_index(har)
            await _loudness(context, har, out)
    except Exception as exc:  # recorded, never raised (A1)
        out.ok, out.error = False, f"the page could not be read: {safe_error(exc)}"
    finally:
        await context.close()
    return out


# Loudness (2.A spec Terms; plan item 4): ACT's own "silent" video has a real
# audio track (-91 dB), so a track's presence is not sound. Decoded with
# OfflineAudioContext in a blank tool page of the same browser, never the
# tested page; audible is a peak above -40 dBFS.
LOUDNESS_MAX_BYTES = 20_000_000
_LOUDNESS_JS = """async (b64) => {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const ctx = new OfflineAudioContext(1, 1, 44100);
  try {
    const buf = await ctx.decodeAudioData(bytes.buffer);
    let peak = 0;
    for (let ch = 0; ch < buf.numberOfChannels; ch++) {
      const d = buf.getChannelData(ch);
      for (let i = 0; i < d.length; i++) { const v = Math.abs(d[i]); if (v > peak) peak = v; }
    }
    return peak > 0 ? 20 * Math.log10(peak) : -200;
  } catch (e) { return null; }
}"""


async def _loudness(context: BrowserContext, har: Path, out: MotionPass) -> None:
    import base64

    from tobi508.capture import media_body

    srcs = sorted({m.src for m in out.media if m.src.startswith(("http:", "https:"))})
    if not srcs:
        return
    tool = await context.new_page()  # about:blank: no page script runs here
    try:
        for src in srcs[:10]:
            body = media_body(har, src)
            if body is None or len(body) > LOUDNESS_MAX_BYTES:
                out.loudness[src] = None
                continue
            got = await tool.evaluate(_LOUDNESS_JS, base64.b64encode(body).decode())
            out.loudness[src] = None if got is None else round(float(got), 1)
    finally:
        await tool.close()


async def _watch(
    page: Page,
    out: MotionPass,
    shots: Path | None,
    rel: Path | None,
    watch_s: float,
    har: Path | None = None,
    prefix: str = "2t",
) -> None:
    out.elements, out.elements_truncated, where = await read_elements(page)
    starts = await _each_frame(
        page, "() => window.__a11yMotion ? window.__a11yMotion.mark0() : null"
    )
    top = next((v for i, _, v in starts if i == 0 and v), None)
    if top is None:
        raise RuntimeError("pass T's hook did not run")
    t0_epoch = top["t0"]
    out.frames_read = sum(1 for _, _, v in starts if v)
    for i, _, v in starts:
        for lr in (v or {}).get("live", []):
            out.live_regions.append(LiveRegion(frame=i, **lr))
        out.carousels += [f"{i}|{c}" for c in (v or {}).get("carousels", [])]
    try:
        out.dialogs_at_start = sorted(
            {d["css"] for d in await page.evaluate(DIALOGS_JS)}
        )
    except Exception:
        pass
    asked: dict[str, list[float]] = {}

    def on_request(req) -> None:
        try:
            if req.method == "GET" and req.resource_type in (
                "fetch",
                "xhr",
                "eventsource",
            ):
                asked.setdefault(req.url, []).append(time.monotonic())
        except Exception:
            pass

    page.on("request", on_request)
    vp = page.viewport_size or {}
    out.viewport = [vp.get("width", 0), vp.get("height", 0)]
    if shots is not None:
        shots.mkdir(parents=True, exist_ok=True)

    regions: dict[str, Region] = {}
    frames_by_key: dict[str, Frame] = {}
    pairs: list[tuple[float, dict[tuple[int, int], list[int]]]] = []
    pngs: list[bytes] = []  # every frame, for each region's states
    reads = list(READS_AT[:-1]) + [watch_s]
    start = time.monotonic()
    prev: Image.Image | None = None
    n = 0
    while True:
        t = time.monotonic() - start
        if reads and t >= reads[0] - 0.05:
            reads.pop(0)
            await _each_frame(
                page, "() => window.__a11yMotion ? window.__a11yMotion.snap() : null"
            )
            out.reads.append(round(time.monotonic() - start, 2))
            for i, fr, media in await _each_frame(
                page, "() => window.__a11yMotion ? window.__a11yMotion.media() : []"
            ):
                at = round(time.monotonic() - start, 2)
                url = fr.url[:500] if i else ""
                out.media += [
                    Media(frame=i, frame_url=url, at=at, **m) for m in media or []
                ]
        shot_t = round(time.monotonic() - start, 2)
        png = await screenshot(page)
        img = Image.open(io.BytesIO(png)).convert("RGB")
        out.frames.append(shot_t)
        if shots is not None:
            path = shots / f"{prefix}-{n:02d}.png"
            path.write_bytes(png)
            out.shots.append(str(path.relative_to(rel)) if rel else str(path))
        if prev is not None and prev.size == img.size:
            pairs.append((shot_t, changed_tiles(prev, img)))
        pngs.append(png)
        prev = img
        n += 1
        if time.monotonic() - start >= watch_s and not reads:
            break
        step = FRAME_STEPS[n % len(FRAME_STEPS)]
        wait = step - (time.monotonic() - start - shot_t)
        if wait > 0:
            await asyncio.sleep(wait)

    page.remove_listener("request", on_request)
    for url, times in asked.items():
        if len(times) >= 2:
            gaps = [b - a for a, b in zip(times, times[1:])]
            out.polls.append(
                Poll(
                    url=url[:500],
                    count=len(times),
                    gap_ms=round(statistics.median(gaps) * 1000),
                    source="watch",
                )
            )
    await _regions(page, pairs, regions, frames_by_key, out)
    long_images = await _long_images(page, har, out) if har is not None else {}
    await _extras(page, regions, frames_by_key, long_images)
    for key, r in regions.items():
        frame = frames_by_key[key]
        try:
            d = await frame.evaluate(
                "(css) => window.__a11yMotion ? window.__a11yMotion.describe(css) : null",
                r.css,
            )
        except Exception:
            d = None
        if not d:
            continue
        epoch0 = t0_epoch
        r.live_off = bool(d.get("live_off"))
        r.sigs = d["sigs"]
        r.colors = d["colors"]
        r.transforms = d["transforms"]
        r.children_moved = bool(d["moved"])
        r.text = d["text"]
        r.connected = d["connected"]
        r.attr_changes = d["attrs"]
        r.attr_list = [
            Change(**{**c, "t": round((c.pop("at") - epoch0) / 1000, 2)})
            for c in d["attr_list"]
        ]
        r.focus_in = [round((t - epoch0) / 1000, 2) for t in d["focus_in"]]
        r.changes = [
            Change(**{**c, "t": round((c.pop("at") - epoch0) / 1000, 2)})
            for c in d["changes"]
        ]
        r.animations = [Animation(**a) for a in d["anims"]]
        gaps = [b - a for a, b in zip(r.changed_at, r.changed_at[1:])]
        r.period_s = round(statistics.median(gaps), 2) if gaps else None
        r.kinds = _kinds(r)
        if r.source not in ("pixels", "dom") and "moving" not in r.kinds:
            r.kinds.append("moving")
        try:
            got = await frame.evaluate(
                "(css) => window.__a11yMotion ? window.__a11yMotion.inside(css) : null",
                r.css,
            )
        except Exception:
            got = None
        local = (got or {}).get("inside", [])
        r.elements = sorted(where[(r.frame, j)] for j in local if (r.frame, j) in where)
        nxt = (got or {}).get("next")
        if not r.elements and nxt is not None:
            here = sorted(i for (f, j), i in where.items() if f == r.frame and j >= nxt)
            r.next_element = here[0] if here else len(out.elements)
    _states(pngs, regions)
    known = [r.css for r in regions.values() if r.frame == 0]
    try:
        out.below = await page.evaluate(
            "(k) => window.__a11yMotion ? window.__a11yMotion.below(k) : []", known
        )
    except Exception:
        out.below = []
    out.regions = sorted(regions.values(), key=lambda r: (r.box[1:2], r.box[0:1]))

    for i, _, facts in await _each_frame(
        page, "() => window.__a11yMotion ? window.__a11yMotion.facts() : null"
    ):
        if not facts:
            continue
        out.audio_connects += facts["audio"]
        out.blink_markup = out.blink_markup or bool(facts.get("blink"))
        out.audio_states += facts.get("audio_states", [])
        out.iframes += facts.get("iframes", [])
        out.dropped_changes += facts["dropped"]
        for f in facts.get("fast", [])[:FAST_KEPT]:
            out.fast_callbacks.append(
                {
                    "frame": i,
                    "t": round((f["at"] - t0_epoch) / 1000, 3),
                    "kind": f["kind"],
                }
            )
        out.fast_animations += [{"frame": i, **a} for a in facts.get("fast_anims", [])]
        counts: dict[tuple[str, int], int] = {}
        for tm in facts["timers"]:
            counts[(tm["kind"], tm["ms"])] = counts.get((tm["kind"], tm["ms"]), 0) + 1
        out.timers += [
            Timer(frame=i, kind=k, ms=ms, count=c)
            for (k, ms), c in sorted(counts.items())
        ]
    try:
        now_dialogs = await page.evaluate(DIALOGS_JS)
        for d in now_dialogs:
            if d["css"] in out.dialogs_at_start:
                continue
            facts = await page.evaluate(_DIALOG_FACTS_JS, d["css"]) or {}
            out.dialogs_opened.append(Dialog(css=d["css"], name=d["name"], **facts))
    except Exception:
        pass
    try:
        fl = await page.evaluate(
            "() => ({ f: window.__a11yLog ? window.__a11yLog.f : [], origin: performance.timeOrigin })"
        )
        for e in fl["f"]:
            at = (fl["origin"] + e["t"] - t0_epoch) / 1000
            if at >= 0 and e["type"] == "focusin":
                out.focus_moves.append(FocusMove(t=round(at, 2), css=e.get("css")))
    except Exception:
        pass


CROP_PAD = 40  # CSS px around a region in its crop
CROP_MIN = (320, 200)  # a crop's least size, for some context around it
CROP_GAP_S = 1.0  # between a region's two crops, as between J1's two frames
CROP_REGIONS = 6


async def _crops(
    page: Page, out: MotionPass, shots: Path, rel: Path | None, prefix: str, every: bool
) -> None:
    """Two pictures cut from the whole page around each top-page region the
    frames do not show whole (or, after the scrolled watch, `every` region),
    CROP_GAP_S apart and with animations running (2.B 1.1.0). Coordinates:
    region boxes are in the viewport as read, so the scroll is added."""
    vw, vh = (out.viewport + [0, 0])[:2] if out.viewport else (0, 0)

    def whole(b: list[int]) -> bool:
        return b[0] >= 0 and b[1] >= 0 and b[0] + b[2] <= vw and b[1] + b[3] <= vh

    todo = [
        r
        for r in out.regions
        if r.frame == 0
        and len(r.box) == 4
        and r.box[2] > 0
        and r.box[3] > 0
        and (every or not whole(r.box))
    ][:CROP_REGIONS]
    if not todo:
        return
    sx, sy = await page.evaluate("() => [scrollX, scrollY]")
    clips = []
    for r in todo:
        x, y, w, h = r.box
        cw, ch = max(w + 2 * CROP_PAD, CROP_MIN[0]), max(h + 2 * CROP_PAD, CROP_MIN[1])
        cx = max(0, x + sx + w / 2 - cw / 2)
        cy = max(0, y + sy + h / 2 - ch / 2)
        clips.append((r, {"x": cx, "y": cy, "width": cw, "height": ch}))
    for k in range(2):
        if k:
            await page.wait_for_timeout(CROP_GAP_S * 1000)
        for i, (r, clip) in enumerate(clips):
            path = shots / f"{prefix}-crop{i + 1}-{'ab'[k]}.png"
            await screenshot(page, path=str(path), clip=clip, full_page=True)
            r.crops.append(str(path.relative_to(rel)) if rel else str(path))


MAX_STATES = 10


def _states(pngs: list[bytes], regions: dict[str, Region]) -> None:
    """How many distinct looks each top-page region's box had over the
    frames (2.B: two states blink; three or more is C1)."""
    boxes = {
        k: r.box
        for k, r in regions.items()
        if r.frame == 0 and len(r.box) == 4 and r.box[2] > 0 and r.box[3] > 0
    }
    if not boxes or not pngs:
        return
    seen: dict[str, set[bytes]] = {k: set() for k in boxes}
    for png in pngs:
        img = Image.open(io.BytesIO(png)).convert("RGB")
        w, h = img.size
        for k, (x, y, bw, bh) in boxes.items():
            crop = (max(0, x), max(0, y), min(w, x + bw), min(h, y + bh))
            if crop[0] < crop[2] and crop[1] < crop[3] and len(seen[k]) <= MAX_STATES:
                seen[k].add(img.crop(crop).tobytes())
    for k, s in seen.items():
        regions[k].states = len(s)


# G152 (2.B Terms): an animated image's frames, delays and loop count, from
# its recorded bytes, decoded with ImageDecoder in a blank tool page.
_IMAGE_JS = """async ([b64, type]) => {
  if (!window.ImageDecoder) return null;
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  try {
    const d = new ImageDecoder({ data: bytes, type });
    await d.tracks.ready;
    const t = d.tracks.selectedTrack;
    const n = t.frameCount;
    let once = 0, min = null;
    for (let i = 0; i < n && i < 500 && n > 1; i++) {
      const r = await d.decode({ frameIndex: i });
      once += (r.image.duration || 0) / 1000;
      // Chrome shows a frame of 10 ms or less for 100 ms (3.A).
      const ms = (r.image.duration || 0) / 1000;
      const shown = ms <= 10 ? 100 : ms;
      min = min === null ? shown : Math.min(min, shown);
      r.image.close();
    }
    return { frames: n, once_ms: Math.round(once), reps: t.repetitionCount === Infinity ? -1 : t.repetitionCount, min_ms: min === null ? null : Math.round(min) };
  } catch (e) { return null; }
}"""
IMAGE_MAX_BYTES = 5_000_000
MOVING_IMAGE_MS = 5000  # TT: "more than 5 seconds"


def _image_type(body: bytes) -> str | None:
    if body[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if body[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "image/webp"
    return None


async def _long_images(page, har: Path, out: MotionPass) -> dict[str, str]:
    """Animated images that play for more than 5 s in all (G152), by URL,
    with the figures as a detail. Recorded in `out.animated_images`."""
    import base64

    from tobi508.capture import media_body

    srcs: list[str] = []
    for _, _, got in await _each_frame(
        page, "() => window.__a11yMotion ? window.__a11yMotion.images() : []"
    ):
        srcs += [s for s in got or [] if s not in srcs]
    found: dict[str, str] = {}
    tool = tool_ctx = None
    try:
        for src in srcs[:30]:
            body = media_body(har, src)
            kind = _image_type(body) if body else None
            if not kind or len(body) > IMAGE_MAX_BYTES:
                continue
            if tool is None:
                tool_ctx, tool = await _secure_tool_page(page)
            got = await tool.evaluate(
                _IMAGE_JS, [base64.b64encode(body).decode(), kind]
            )
            if not got or got["frames"] < 2:
                continue
            total = None if got["reps"] < 0 else got["once_ms"] * (got["reps"] + 1)
            out.animated_images.append({"src": src[:500], **got, "total_ms": total})
            if total is None or total > MOVING_IMAGE_MS:
                found[src] = f"animated image, {got['frames']} frames, " + (
                    "loops forever" if total is None else f"{total / 1000:g} s in all"
                )
    finally:
        if tool_ctx is not None:
            await tool_ctx.close()
    return found


TOOL_URL = "http://localhost/a11y-tool"


async def _secure_tool_page(page):
    """A blank page in its own fresh context of the same browser, at
    http://localhost (a secure context: ImageDecoder exists only there, not
    on about:blank), answered by a route: no network, no page script."""
    ctx = await page.context.browser.new_context()
    await ctx.route(
        TOOL_URL,
        lambda r: r.fulfill(
            status=200,
            content_type="text/html",
            body="<!doctype html><title>tool</title>",
        ),
    )
    tool = await ctx.new_page()
    await tool.goto(TOOL_URL)
    return ctx, tool


async def _extras(
    page, regions: dict[str, Region], frames_by_key, long_images=None
) -> None:
    """Regions for motion the frames could not show (2.B Terms)."""
    for i, frame in enumerate(page.frames):
        known = [r.css for r in regions.values() if r.frame == i]
        try:
            got = await frame.evaluate(
                "([k, li]) => window.__a11yMotion ? window.__a11yMotion.extras(k, li) : []",
                [known, long_images or {}],
            )
        except Exception:
            continue
        for e in got or []:
            key = f"{i}|{e['css']}"
            if key in regions or len(regions) >= MAX_REGIONS:
                continue
            regions[key] = Region(
                key=key,
                frame=i,
                frame_url=frame.url[:500] if i else "",
                css=e["css"],
                tag=e["tag"],
                content_css=e["css"],
                box=e["box"],
                source=e["source"],
                source_detail=e["detail"][:200],
            )
            frames_by_key[key] = frame


async def _regions(page, pairs, regions, frames_by_key, out: MotionPass) -> None:
    """Regions from the whole watch (2.C Terms): every tile that changed in
    any frame, with the union of its changed pixels, grouped and mapped once
    at the end. Mapping each frame on its own split one region in two when
    its changed pixels moved (a spinning square, slides taking turns), and a
    frame where most of the page changed (a dialog's backdrop, a scroll) would
    join every region into one, so such frames are noted, not mapped."""
    total = 0
    if pairs:
        w, h = out.viewport or [0, 0]
        total = max(1, -(-w // TILE) * -(-h // TILE))
    union: dict[tuple[int, int], list[int]] = {}
    kept = []
    for t, tiles in pairs:
        if len(tiles) > total * PAGE_CHANGE:
            out.page_changes.append(t)
            continue
        kept.append((t, tiles))
        for k, b in tiles.items():
            u = union.get(k)
            union[k] = (
                list(b)
                if u is None
                else [
                    min(u[0], b[0]),
                    min(u[1], b[1]),
                    max(u[2], b[2]),
                    max(u[3], b[3]),
                ]
            )
    owner: dict[tuple[int, int], str] = {}
    for group in components(set(union))[:MAX_COMPONENTS]:
        ordered = sorted(group)
        hits = 0
        for frame, info in await _map(page.main_frame, [union[t] for t in ordered]):
            index = page.frames.index(frame) if frame in page.frames else -1
            key = f"{index}|{info['css']}"
            if key not in regions:
                if len(regions) >= MAX_REGIONS:
                    out.regions_capped = True
                    continue
                regions[key] = Region(
                    key=key,
                    frame=index,
                    frame_url=frame.url[:500] if index else "",
                    css=info["css"],
                    tag=info["tag"],
                    content_css=info["css"],
                    carousel=info["carousel"],
                    covered=info["covered"],
                    box=info["box"],
                )
                frames_by_key[key] = frame
            r = regions[key]
            if info.get("part") and info["part"] not in r.parts:
                r.parts.append(info["part"])
            for i in info["idx"]:
                owner[ordered[i]] = key
                if len(r.changed_boxes) < MAX_BOXES:
                    r.changed_boxes.append(union[ordered[i]])
            hits += len(info["idx"])
        out.unmapped_tiles += len(group) - hits
    if len(components(set(union))) > MAX_COMPONENTS:
        out.regions_capped = True
    for t, tiles in kept:
        counts: dict[str, int] = {}
        for k in tiles:
            if k in owner:
                counts[owner[k]] = counts.get(owner[k], 0) + 1
        for key, n in counts.items():
            regions[key].changed_at.append(t)
            regions[key].tiles = max(regions[key].tiles, n)


# ── Mechanism probe evidence (2.C spec section 2; 2.A and 2.B use it) ──────
# Filled by mechanism.probe; an instance it did not reach has
# `probed=False`, and the checks' rows say so (K7).


class Candidate(BaseModel):
    element: int  # Element.i
    window: str  # top | before | after | inside
    kind: str  # control | text
    # stopped | slowed | no_effect | unreliable | unreachable | untried, or not
    # pressed: field (needs a value, K5) | not_operable (a link that goes
    # somewhere: following it is not pausing)
    result: str = "untried"
    focus_only: str | None = None  # the focus-only probe's result, if run
    key: str | None = None  # a key combination from J2 that was pressed
    keys: str = ""  # how to reach it ("Tab 4 times, then Enter")


class Probe(BaseModel):
    """The mechanism probe for one content (an instance)."""

    probed: bool = False
    candidates: list[Candidate] = Field(default_factory=list)
    reads_failed: bool = False
    untried: int = 0  # controls not tried (time, or the per-content cap)
    cannot_place: bool = False  # no element inside the content: windows unknown
    cannot_try: str = ""  # K5: a mechanism the tool may not try, named


async def _scrolled_watch(ctx: Any, mp: MotionPass, har: Path, keep: bool) -> None:
    """Plan Q3: one more watch, with the first hint below the first screen
    scrolled into view (content that starts only when seen). New regions
    join pass T's, marked scrolled."""
    target = mp.below[0]
    second = await pass_t(
        ctx.open_motion,
        har if har.exists() else None,
        ctx.shots if keep else None,
        ctx.rel,
        scroll_to=target,
        prefix="2s",
    )
    mp.scrolled_watch = target
    if not second.ok:
        return
    have = {r.key for r in mp.regions}
    for r in second.regions:
        if r.key not in have:
            r.scrolled = True
            mp.regions.append(r)


SETTLE_IGNORE_FROM_S = 5.0  # still changing then: it keeps changing


def settle_ignore(mp: MotionPass) -> dict[str, list[str]]:
    """Regions still changing by themselves at the end of the watch, by frame
    ("" for the top page, else the frame's URL), for the settle rule to stop
    waiting on (T1 (b)). Only content that keeps changing: a change that
    ends (a late load) is waited for as before."""
    out: dict[str, list[str]] = {}
    if not mp.ok:
        return out
    for r in mp.regions:
        if r.source != "pixels" or (
            r.changed_at and r.changed_at[-1] >= SETTLE_IGNORE_FROM_S
        ):
            out.setdefault(r.frame_url if r.frame else "", []).append(r.css)
    return out


async def collect(ctx: Any, keep_shots: bool = True) -> MotionPass:
    """Pass T once per call, shared by the 2.x checks (ctx.cache["motion"])."""
    if "motion" in ctx.cache:
        return ctx.cache["motion"]
    started = ctx.cache.get("motion_task")  # the pipeline's, beside the walk
    if started is not None and started is not asyncio.current_task():
        return await started
    if getattr(ctx, "open_motion", None) is None:
        mp = MotionPass(ok=False, error="the page could not be watched in this run")
    elif ctx.out_of_time():
        mp = MotionPass(
            ok=False,
            error="the run reached its time limit before the page could be watched",
        )
    else:
        har = ctx.rel / "evidence" / "page.har.zip"
        mp = await pass_t(
            ctx.open_motion,
            har if har.exists() else None,
            ctx.shots if keep_shots else None,
            ctx.rel,
        )
        if mp.ok and mp.below and not ctx.out_of_time():
            await _scrolled_watch(ctx, mp, har, keep_shots)
    mp.browser = getattr(ctx, "motion_browser", "")
    ctx.cache["motion"] = mp
    return mp
