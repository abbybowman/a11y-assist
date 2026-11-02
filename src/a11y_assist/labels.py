"""Pass L: form components, their visible labels and ANDI's output, shared by
5.A and 5.C (docs/rules/5c-programmatic-label.md section 2). One fresh load
after the walk: inventory every form component of the top document, read
its label candidates, table headers and list context, focus each
data-entry field and take a clipped image of it with what is around it,
then inject the vendored ANDI and read its output. Fields that appear only
after interaction are read the same way at the end of 4.F's pass R and
5.D's fill pass replays (`read_revealed`). Facts only; no outcome is
decided here (CLAUDE.md principle 2).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from a11y_assist.andi import andi_output, inject_andi, install_andi_routes
from a11y_assist.traverse import PATH_JS, Session, screenshot

COMPONENT_MAX = 60
# The image and the nearby-text region around a field (5.A spec section 2).
LEFT, UP, RIGHT, DOWN = 240, 120, 160, 160
NEARBY_CHARS = 400

_SHARED_JS = """
  const doc = document;
  const SEL = 'input,select,textarea,button,[role=button],[role=checkbox],[role=radio],[role=switch],' +
    '[role=combobox],[role=textbox],[role=searchbox],[role=slider],[role=spinbutton],[role=listbox]';
  const vis = (e) => !!(e && e.checkVisibility && e.checkVisibility({ visibilityProperty: true }));
  const shown = (e) => {
    if (!vis(e)) return false;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return false;
    const cs = getComputedStyle(e);
    if (parseFloat(cs.opacity) < 0.1) return false;
    if ((cs.clip || '').startsWith('rect(0') || (cs.clipPath || '').includes('inset(50%')) return false;
    return true;
  };
  const txt = (e) => (e ? (e.innerText || e.textContent || '') : '').replace(/\\s+/g, ' ').trim();
  const comps = () => Array.from(doc.querySelectorAll(SEL)).filter((el) => {
    if (el.closest('#ANDI508')) return false;
    const t = (el.type || '').toLowerCase();
    if (el.tagName === 'INPUT' && ['hidden', 'image'].includes(t)) return false;
    if (el.disabled || el.getAttribute('aria-disabled') === 'true') return false;
    return vis(el);
  });
  const ids = (el, a) => (el.getAttribute(a) || '').split(/\\s+/).filter(Boolean)
    .map((id) => doc.getElementById(id)).filter(Boolean);
  const labelEls = (el) => {
    const out = [...(el.labels ? Array.from(el.labels) : []), ...ids(el, 'aria-labelledby')];
    return out;
  };
  const groupEls = (el) => {
    const fs = el.closest('fieldset');
    const lg = fs && Array.from(fs.children).find((c) => c.tagName === 'LEGEND');
    if (lg) return [lg];
    const g = el.closest('[role=radiogroup],[role=group]');
    return g ? ids(g, 'aria-labelledby') : [];
  };
"""

COMPONENTS_JS = (
    "(function () {"
    + PATH_JS
    + _SHARED_JS
    + """
  const els = comps();
  window.__a11yLabelEls = els;
  const ownText = (li) => Array.from(li.childNodes).filter((n) => n.nodeType === 3)
    .map((n) => n.textContent).join(' ').replace(/\\s+/g, ' ').trim();
  const headers = (el) => {
    const cell = el.closest('td,th');
    if (!cell || !cell.closest('table')) return [];
    const out = [];
    const hdr = (cell.getAttribute('headers') || '').split(/\\s+/).filter(Boolean)
      .map((id) => doc.getElementById(id)).filter(Boolean);
    if (hdr.length) return hdr.map(txt).filter(Boolean);
    const tr = cell.parentElement, table = cell.closest('table');
    const rowTh = Array.from(tr.children).find((c) => c.tagName === 'TH' && c !== cell);
    if (rowTh) out.push(txt(rowTh));
    const idx = Array.from(tr.children).indexOf(cell);
    for (const row of Array.from(table.rows)) {
      if (row === tr) break;
      const c = row.children[idx];
      if (c && c.tagName === 'TH') { out.push(txt(c)); break; }
    }
    return out.filter(Boolean);
  };
  return els.map((el, i) => {
    const tag = el.tagName.toLowerCase(), type = (el.type || '').toLowerCase(), role = el.getAttribute('role') || '';
    const button = tag === 'button' || (tag === 'input' && ['submit', 'reset', 'button'].includes(type)) || role === 'button';
    const option = type === 'radio' || type === 'checkbox' || ['radio', 'checkbox', 'switch'].includes(role);
    let group = null;
    if (type === 'radio' || type === 'checkbox') group = (el.form ? path(el.form) : '') + ':' + type + ':' + (el.name || path(el));
    else if (role === 'radio') { const g = el.closest('[role=radiogroup]'); group = g ? 'rg:' + path(g) : null; }
    const r = el.getBoundingClientRect();
    return {
      i, css: path(el), tag, type, role, button, option, group,
      form: (el.form || el.closest('form')) ? path(el.form || el.closest('form')) : '',
      readonly: el.readOnly === true || el.getAttribute('aria-readonly') === 'true',
      required: el.required === true || el.getAttribute('aria-required') === 'true',
      labels: labelEls(el).map(txt).filter(Boolean),
      group_labels: groupEls(el).map(txt).filter(Boolean),
      placeholder: el.getAttribute('placeholder') || '',
      aria_label: el.getAttribute('aria-label') || '',
      title: el.getAttribute('title') || '',
      own_text: button ? (txt(el) || el.value || '') : '',
      table_headers: headers(el),
      list_text: Array.from((function* () { for (let li = el.closest('li'); li; li = li.parentElement && li.parentElement.closest('li')) yield li; })())
        .map(ownText).filter(Boolean),
      box: [Math.round(r.left + scrollX), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)],
    };
  });
})()"""
)

# Focus component i of the last COMPONENTS_JS read; what is visible around it.
FOCUS_JS = (
    "(function (i) {"
    + PATH_JS
    + _SHARED_JS
    + """
  const els = window.__a11yLabelEls || [];
  const el = els[i];
  if (!el) return null;
  el.scrollIntoView({ block: 'center', inline: 'nearest' });
  try { el.focus({ preventScroll: true }); } catch (e) {}
  const r = el.getBoundingClientRect();
  const vw = innerWidth, vh = innerHeight;
  const reg = { l: Math.max(0, r.left - LEFT), t: Math.max(0, r.top - UP),
                r: Math.min(vw, r.right + RIGHT), b: Math.min(vh, r.bottom + DOWN) };
  const inReg = (b) => b.right > reg.l && b.left < reg.r && b.bottom > reg.t && b.top < reg.b;
  const mine = new Set([...labelEls(el), ...groupEls(el)]);
  const others = [];
  for (const o of els) {
    if (o === el) continue;
    others.push(o);
    for (const x of labelEls(o)) if (!mine.has(x)) others.push(x);
  }
  // Fieldsets that do not hold this field belong to other fields (their
  // legend and content); outside the field's form is not its cue.
  for (const fs of doc.querySelectorAll('fieldset')) if (!fs.contains(el)) others.push(fs);
  const form = el.form || el.closest('form');
  const inOther = (n) => others.some((o) => o === n || o.contains(n)) || (form && !form.contains(n));
  const labels = [...labelEls(el), ...groupEls(el)].map((l) => ({
    text: txt(l), shown: shown(l) && inReg(l.getBoundingClientRect()) }));
  const near = [];
  const tw = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
  const cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2;
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const p = n.parentElement;
    if (!p || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'OPTION', 'TEXTAREA'].includes(p.tagName)) continue;
    if (p.closest('#ANDI508') || el.contains(p) || inOther(p) || !shown(p)) continue;
    // Section headings need no association (5.C p. 27 Note 5): not field text.
    if (p.closest('h1,h2,h3,h4,h5,h6,[role=heading]')) continue;
    const t = n.textContent.replace(/\\s+/g, ' ').trim();
    if (!t) continue;
    const range = doc.createRange(); range.selectNodeContents(n);
    const b = range.getBoundingClientRect();
    if (!b.width || !inReg(b)) continue;
    near.push({ t, d: Math.hypot((b.left + b.right) / 2 - cx, (b.top + b.bottom) / 2 - cy) });
  }
  near.sort((a, b) => a.d - b.d);
  // Visible labels of other fields in the region: a set of fields (a phone
  // number in three boxes) may share one label (F82); 5.A's J1 may quote them.
  const nbr = [];
  for (const o of els) {
    if (o === el) continue;
    for (const l of labelEls(o)) {
      const t = txt(l);
      if (t && shown(l) && inReg(l.getBoundingClientRect()) && !nbr.includes(t)) nbr.push(t);
    }
  }
  return {
    focused: doc.activeElement === el,
    labels, nearby: near.map((x) => x.t), nearby_other: nbr.slice(0, 6),
    placeholder_shown: !!el.getAttribute('placeholder') && !el.value,
    // Viewport coordinates: a viewport screenshot's clip is relative to it.
    clip: { x: reg.l, y: reg.t, width: Math.max(1, reg.r - reg.l), height: Math.max(1, reg.b - reg.t) },
  };
})""".replace("LEFT", str(LEFT))
    .replace("UP", str(UP))
    .replace("RIGHT", str(RIGHT))
    .replace("DOWN", str(DOWN))
)


class Comp(BaseModel):
    n: int
    css: str
    tag: str = ""
    type: str = ""
    role: str = ""
    button: bool = False
    option: bool = False
    group: str | None = None
    form: str = ""  # form owner's path; "" outside any form (5.B)
    readonly: bool = False
    required: bool = False
    labels: list[str] = Field(default_factory=list)
    group_labels: list[str] = Field(default_factory=list)
    placeholder: str = ""
    aria_label: str = ""
    title: str = ""
    own_text: str = ""
    table_headers: list[str] = Field(default_factory=list)
    list_text: list[str] = Field(default_factory=list)
    # With focus (data-entry fields only)
    focused: bool | None = None
    label_shown: list[dict[str, Any]] = Field(default_factory=list)
    nearby: list[str] = Field(default_factory=list)
    nearby_other: list[str] = Field(default_factory=list)  # other fields' labels
    placeholder_shown: bool = False
    image: str | None = None
    andi: dict[str, Any] | None = None  # name, desc, group, dangers, warnings
    origin: str = "load"  # or how a replay revealed it
    tab_index: int | None = None  # P1 step index, when it is a walk stop

    @property
    def entry(self) -> bool:
        """A data-entry field (5.A): takes input; not a button, not read-only."""
        return not self.button and not self.readonly

    @property
    def kind(self) -> str:
        if self.button:
            return "button"
        if self.option:
            return self.type or self.role or "option"
        if self.tag == "select":
            return "drop-down"
        return self.role or (
            "text field" if self.tag in ("input", "textarea") else self.tag
        )


class LabelsPass(BaseModel):
    components: list[Comp] = Field(default_factory=list)
    andi_ran: bool = False
    andi_version: str | None = None
    andi_aborted: list[str] = Field(default_factory=list)
    incomplete: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    revealed_from: list[str] = Field(default_factory=list)


def _norm(t: str) -> str:
    return " ".join((t or "").split())


async def read_session(
    ctx, s: Session, origin: str, images: bool, tag: str
) -> LabelsPass:
    """Inventory, focus reads and images, then ANDI, on one session (its
    page is changed by ANDI: call this last on a session)."""
    out = LabelsPass()
    page = s.page
    try:
        got = await s.traversal.reader.evaluate_top(COMPONENTS_JS)
    except Exception as exc:
        out.incomplete.append(
            f"The form fields could not be read ({type(exc).__name__})."
        )
        return out
    # Forms inside frames are not read yet: say so, never treat them as absent.
    framed = 0
    for fr in page.frames[1:]:
        try:
            framed += await fr.evaluate(
                "document.querySelectorAll('input:not([type=hidden]),select,textarea,button').length"
            )
        except Exception:
            continue
    if framed:
        out.incomplete.append(
            f"{framed} form field(s) or button(s) inside frames were not checked."
        )
    for c in got or []:
        out.components.append(
            Comp(
                n=len(out.components) + 1,
                origin=origin,
                **{k: v for k, v in c.items() if k not in ("i", "box")},
            )
        )
    if len(out.components) > COMPONENT_MAX:
        out.incomplete.append(
            f"The page has {len(out.components)} form fields and buttons; only the first {COMPONENT_MAX} were checked."
        )
        out.components = out.components[:COMPONENT_MAX]
    for i, c in enumerate(out.components):
        if not c.entry:
            continue
        if ctx.out_of_time():
            out.incomplete.append(
                "The run time limit was reached before every form field was looked at."
            )
            break
        try:
            r = await s.traversal.reader.evaluate_top(f"{FOCUS_JS}({i})")
        except Exception:
            r = None
        if not r:
            continue
        c.focused = r.get("focused")
        c.label_shown = r.get("labels") or []
        c.placeholder_shown = bool(r.get("placeholder_shown"))
        near, total = [], 0
        for t in r.get("nearby") or []:
            if total >= NEARBY_CHARS:
                break
            near.append(t)
            total += len(t)
        c.nearby = near
        c.nearby_other = r.get("nearby_other") or []
        if images:
            try:
                ctx.shots.mkdir(parents=True, exist_ok=True)
                p = ctx.shots / f"5a-{tag}-{c.n}.png"
                await screenshot(
                    page, path=str(p), clip=r["clip"], animations="disabled"
                )
                c.image = p.resolve().relative_to(ctx.rel.resolve()).as_posix()
            except Exception:
                c.image = None
    # ANDI last: it changes the page.
    if ctx.third_party is not None:
        try:
            # Mark each component before ANDI wraps the page (its wrapper
            # changes CSS paths that do not start at an id): match by mark.
            await s.traversal.reader.evaluate_top(
                "(window.__a11yLabelEls || []).forEach((e, i) => e.setAttribute('data-a11y-c', String(i)))"
            )
            out.andi_aborted = await install_andi_routes(
                s.traversal.context, ctx.third_party
            )
            out.andi_version = await inject_andi(page, ctx.third_party)
            await page.wait_for_timeout(500)
            rows = await andi_output(page)
            if rows is not None:
                out.andi_ran = True
                by_mark = {r.get("mark"): r for r in rows if r.get("mark") is not None}
                for i, c in enumerate(out.components):
                    c.andi = by_mark.get(str(i))
        except Exception as exc:
            out.notes.append(f"ANDI could not run on this page ({type(exc).__name__}).")
    return out


def wanted(ctx) -> bool:
    return bool({"5.A", "5.B", "5.C"} & set(ctx.selected))


async def read_revealed(ctx, s: Session, origin: str) -> None:
    """At the end of a replay that revealed content (4.F pass R, 5.D pass F):
    read its form components with ANDI, for 5.A and 5.C (spec 5.C section 2,
    fields revealed by interaction). Only when 5.A or 5.C runs in this call;
    call it last on the session (ANDI changes the page)."""
    if not wanted(ctx) or ctx.out_of_time():
        return
    try:
        got = await read_session(
            ctx, s, origin, True, f"r{len(ctx.cache.get('labels-revealed', [])) + 1}"
        )
    except Exception:
        return
    ctx.cache.setdefault("labels-revealed", []).append(got)


async def labels_pass(ctx, walk) -> LabelsPass:
    """Pass L, once per call (5.A and 5.C both read it)."""
    if "labels-pass" in ctx.cache:
        return ctx.cache["labels-pass"].model_copy(deep=True)
    from a11y_assist.traverse import open_session

    s = await open_session(ctx.new_page, ctx.quiet_ms)
    try:
        lp = await read_session(ctx, s, "load", True, "l")
    finally:
        await s.close()
    seen = {c.css for c in lp.components}
    for extra in ctx.cache.get("labels-revealed", []):
        for c in extra.components:
            if c.css in seen:
                continue
            seen.add(c.css)
            lp.components.append(c.model_copy(update={"n": len(lp.components) + 1}))
            if c.origin not in lp.revealed_from:
                lp.revealed_from.append(c.origin)
    if walk is not None:
        idx = {
            st.stop.css_path: i
            for i, st in enumerate(walk.p1.steps)
            if st.stop.kind == "element" and not st.stop.frame_chain
        }
        for c in lp.components:
            c.tab_index = idx.get(c.css)
    ctx.cache["labels-pass"] = lp
    return lp.model_copy(deep=True)
