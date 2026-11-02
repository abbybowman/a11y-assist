"""Other pages of the same site, read once for 9.A, 9.B and 9.C.

Each page (the tested page and every page the caller named in
`other_pages`) gets one fresh load of its own HAR and one DOM read of its
rendered content in reading order: *units* (text, headings, images with alt
text, controls) and *regions* (banner, navigation, search, complementary,
contentinfo, main). The read is cached in `RunContext.cache["site"]` so the
three checks share it. Facts only: what repeats and what matches; the specs
(docs/rules/9a-bypass.md Terms) decide what that means.

Page content never chooses a page to read (CLAUDE.md principle 5): the pages
are the caller's.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from a11y_assist.traverse import PATH_JS, NewPage

UNIT_CAP = 600  # units read per page (9.A spec section 2)

# Defines units(cap): the page's rendered content in reading order. Shared by
# the site read and 9.A's landing read, so both number units the same way.
UNITS_FN = (
    PATH_JS
    + r"""
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const shown = (el) => {
    if (getComputedStyle(el).display === 'contents') return true;
    return el.checkVisibility ? el.checkVisibility({ visibilityProperty: true })
                              : el.getClientRects().length > 0;
  };
  const CONTROL = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, ' +
    '[role=link], [role=button], [role=menuitem], [role=tab], [role=checkbox], [role=radio], ' +
    '[role=switch], [role=combobox], [role=searchbox], [role=textbox], [role=option], ' +
    '[tabindex]:not([tabindex^="-"])';
  const NOT_LANDMARK_ANCESTOR = 'article, aside, main, nav, section, [role=main]';
  const regionRole = (el) => {
    const r = (el.getAttribute('role') || '').trim().split(/\s+/)[0];
    if (['banner', 'navigation', 'search', 'complementary', 'contentinfo', 'main'].includes(r)) return r;
    if (r) return null;
    const t = el.tagName;
    if (t === 'NAV') return 'navigation';
    if (t === 'ASIDE') return 'complementary';
    if (t === 'MAIN') return 'main';
    if (t === 'SEARCH') return 'search';
    if ((t === 'HEADER' || t === 'FOOTER') && !(el.parentElement && el.parentElement.closest(NOT_LANDMARK_ANCESTOR)))
      return t === 'HEADER' ? 'banner' : 'contentinfo';
    return null;
  };
  const textOf = (ids) => norm(ids.split(/\s+/).map((i) => document.getElementById(i))
    .filter(Boolean).map((e) => e.textContent).join(' '));
  const label = (el) => norm(el.getAttribute('aria-label')) ||
    (el.getAttribute('aria-labelledby') ? textOf(el.getAttribute('aria-labelledby')) : '');
  const controlRole = (el) => {
    const r = (el.getAttribute('role') || '').trim().split(/\s+/)[0];
    if (r) return r;
    const t = el.tagName, type = (el.type || '').toLowerCase();
    if (t === 'A') return 'link';
    if (t === 'BUTTON' || t === 'SUMMARY') return 'button';
    if (t === 'SELECT') return el.multiple || el.size > 1 ? 'listbox' : 'combobox';
    if (t === 'TEXTAREA') return 'textbox';
    if (t === 'INPUT') {
      if (['button', 'submit', 'reset', 'image'].includes(type)) return 'button';
      if (type === 'checkbox' || type === 'radio') return type;
      if (type === 'range') return 'slider';
      if (type === 'search') return 'searchbox';
      return 'textbox';
    }
    return 'generic';
  };
  const nameOf = (el) => {
    const l = label(el);
    if (l) return l;
    const t = el.tagName, type = (el.type || '').toLowerCase();
    if (t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') {
      if (['button', 'submit', 'reset'].includes(type)) return norm(el.value);
      if (type === 'image') return norm(el.alt);
      const labs = el.labels ? Array.from(el.labels).map((x) => x.textContent).join(' ') : '';
      return norm(labs) || norm(el.getAttribute('placeholder')) || norm(el.title);
    }
    const parts = [];
    const visit = (n) => {
      if (n.nodeType === 3) { parts.push(n.textContent); return; }
      if (n.nodeType !== 1 || !shown(n)) return;
      if (n.tagName === 'IMG') { parts.push(n.getAttribute('alt') || ''); return; }
      if (n.tagName === 'svg' || n.tagName === 'SVG') {
        const tl = n.querySelector('title'); if (tl) parts.push(tl.textContent); return;
      }
      for (const c of n.childNodes) visit(c);
    };
    visit(el);
    return norm(parts.join(' ')) || norm(el.title);
  };
  const tabbable = (el) => {
    const ti = el.getAttribute('tabindex');
    if (ti !== null && ti.trim() !== '' && parseInt(ti, 10) < 0) return false;
    if (el.disabled) return false;
    return el.matches('a[href], button, input:not([type="hidden"]), select, textarea, summary') ||
      (ti !== null && ti.trim() !== '' && parseInt(ti, 10) >= 0);
  };
  const units = (cap) => {
    const out = [], regions = [], counts = {}, els = [];
    let truncated = false;
    const box = (el) => {
      const r = el.getBoundingClientRect();
      return [Math.round(r.x + scrollX), Math.round(r.y + scrollY), Math.round(r.width), Math.round(r.height)];
    };
    const push = (el, u, chain) => {
      if (out.length >= cap) { truncated = true; return false; }
      els.push(el);
      const inner = chain.filter((k) => !k.startsWith('main|'));
      out.push(Object.assign({ i: out.length, css: path(el), regions: chain.slice(),
        region_role: inner.length ? inner[inner.length - 1].split('|')[0] : '',
        in_main: chain.some((k) => k.startsWith('main|')), box: box(el),
        keys: norm(el.getAttribute('accesskey') || el.getAttribute('aria-keyshortcuts')) }, u));
      return true;
    };
    const walk = (el, chain) => {
      if (truncated || !shown(el)) return;
      const rr = regionRole(el);
      if (rr) {
        counts[rr] = (counts[rr] || 0) + 1;
        const key = rr + '|' + (label(el) || (el.id ? '#' + el.id : '@' + counts[rr]));
        regions.push({ key, role: rr, css: path(el), box: box(el) });
        chain = chain.concat([key]);
      }
      const t = el.tagName;
      if (t === 'IFRAME' || t === 'FRAME') { push(el, { kind: 'frame', role: 'frame', text: '', name: norm(el.title) }, chain); return; }
      if (el.matches(CONTROL)) {
        const name = nameOf(el);
        const raw = el.getAttribute('href');
        push(el, { kind: 'control', role: controlRole(el), name, text: name.toLowerCase().slice(0, 200),
          href: t === 'A' && raw !== null ? el.href : '', href_attr: raw === null ? null : raw,
          submit: !!el.form && (el.type || '').toLowerCase() === 'submit', stop: tabbable(el),
          id: el.id || '' }, chain);
        return;
      }
      const hm = /^H([1-6])$/.exec(t);
      if (hm || el.getAttribute('role') === 'heading') {
        const text = norm(el.textContent);
        if (text) push(el, { kind: 'heading', role: 'heading', level: hm ? +hm[1] : +(el.getAttribute('aria-level') || 2),
          name: text, text: text.toLowerCase().slice(0, 200) }, chain);
        return;
      }
      if (t === 'IMG') {
        const alt = norm(el.getAttribute('alt'));
        if (alt) push(el, { kind: 'image', role: 'img', name: alt, text: alt.toLowerCase().slice(0, 200) }, chain);
        return;
      }
      if (t === 'SCRIPT' || t === 'STYLE' || t === 'TEMPLATE' || t === 'NOSCRIPT') return;
      let own = '';
      for (const c of el.childNodes) if (c.nodeType === 3) own += ' ' + c.textContent;
      own = norm(own);
      if (own) push(el, { kind: 'text', role: 'text', name: own.slice(0, 300), text: own.toLowerCase().slice(0, 200) }, chain);
      for (const c of el.children) walk(c, chain);
    };
    if (document.body) walk(document.body, []);
    return { units: out, regions, truncated, url: location.href, els };
  };
"""
)

READ_JS = "(cap) => {" + UNITS_FN + " const r = units(cap); delete r.els; return r; }"


class Unit(BaseModel):
    i: int
    kind: str  # text | heading | image | control | frame
    role: str
    text: str  # the text key: lower case, spaces collapsed
    name: str = ""
    css: str
    regions: list[str] = Field(default_factory=list)  # region keys, outer first
    region_role: str = ""  # innermost region other than main
    in_main: bool = False
    box: list[int] = Field(default_factory=list)  # page x, y, width, height
    href: str = ""
    href_attr: str | None = None
    submit: bool = False
    stop: bool = False  # natively tabbable or tabindex >= 0
    id: str = ""
    level: int | None = None
    keys: str = ""  # accesskey or aria-keyshortcuts


class Region(BaseModel):
    key: str  # role|label, role|#id or role|@n
    role: str
    css: str
    box: list[int] = Field(default_factory=list)


class PageRead(BaseModel):
    n: int  # 0: the tested page; 1..5: the caller's other pages
    url: str
    units: list[Unit] = Field(default_factory=list)
    regions: list[Region] = Field(default_factory=list)
    truncated: bool = False
    error: str = ""


class SiteRead(BaseModel):
    pages: list[PageRead]

    @property
    def main(self) -> PageRead:
        return self.pages[0]

    @property
    def others(self) -> list[PageRead]:
        return self.pages[1:]

    @property
    def errors(self) -> list[str]:
        return [
            f"{page_label(p)} could not be read: {p.error}"
            for p in self.pages
            if p.error
        ]


def page_label(p: PageRead) -> str:
    return "the tested page" if p.n == 0 else f"other page {p.n}"


async def read_page(n: int, url: str, new_page: NewPage) -> PageRead:
    """One fresh load of a page's HAR and one DOM read (no key pressed)."""
    try:
        context, page = await new_page()
    except Exception as exc:
        return PageRead(n=n, url=url, error=type(exc).__name__)
    try:
        await page.wait_for_load_state("load")
        data = await page.evaluate(READ_JS, UNIT_CAP)
        return PageRead(
            n=n,
            url=data["url"],
            units=[Unit(**u) for u in data["units"]],
            regions=[Region(**r) for r in data["regions"]],
            truncated=data["truncated"],
        )
    except Exception as exc:
        return PageRead(n=n, url=url, error=type(exc).__name__)
    finally:
        await context.close()


async def site_read(ctx: Any) -> SiteRead:
    """The tested page and every other page, read once per run (cached)."""
    if "site" not in ctx.cache:
        reads = await asyncio.gather(
            read_page(0, "", ctx.new_page),
            *(read_page(p.n, p.final_url, p.new_page) for p in ctx.pages),
        )
        ctx.cache["site"] = SiteRead(pages=list(reads))
    return ctx.cache["site"]


# ── Facts about repetition and matching (no outcomes) ───────────────────────


def repeated_flags(site: SiteRead) -> list[bool]:
    """Per unit of the tested page: its text key appears on another page, or
    it sits in a region (not main) that another page also has (9.A Terms)."""
    texts: set[str] = set()
    regions: set[str] = set()
    for p in site.others:
        texts |= {u.text for u in p.units if u.text}
        regions |= {r.key for r in p.regions if r.role != "main"}
    return [
        bool(u.text and u.text in texts)
        or any(k in regions for k in u.regions if not k.startswith("main|"))
        for u in site.main.units
    ]


def norm_href(href: str, page_url: str = "") -> str:
    """A link destination for matching: absolute, fragment dropped unless the
    link is to a place on its own page, trailing slash ignored."""
    if not href:
        return ""
    base, _, frag = href.partition("#")
    own = page_url.split("#")[0]
    if frag and own and base == own:
        return "#" + frag
    return base.rstrip("/")


def before(a: list[int], b: list[int]) -> bool:
    """Visual order (9.B Terms): a's box ends above b's, or they share a line
    and a is to the left. Boxes are page x, y, width, height."""
    if not a or not b or a[2] * a[3] == 0 or b[2] * b[3] == 0:
        return False
    if a[1] + a[3] <= b[1] + 1:
        return True
    overlap = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    if overlap >= 0.5 * min(a[3], b[3]):
        return a[0] + a[2] <= b[0] + 1
    return False


def pair_in_order(left: list[tuple[str, int]], right: list[tuple[str, int]]):
    """Pair items with equal keys, the k-th with the k-th. Each item is (key,
    position); returns (left position, right position) pairs."""
    from collections import defaultdict

    slots: dict[str, list[int]] = defaultdict(list)
    for k, pos in right:
        slots[k].append(pos)
    taken: dict[str, int] = defaultdict(int)
    out = []
    for k, pos in left:
        j = taken[k]
        if j < len(slots[k]):
            out.append((pos, slots[k][j]))
            taken[k] = j + 1
    return out
