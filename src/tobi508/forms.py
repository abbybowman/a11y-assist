"""Form fields, shared by the form tests (5.D, 5.F, 5.G): which P1 stops
are fields, arriving at one with Tab, and page reads run on a field (label,
kind, value, own widget, the text before it; the visible text outside its
own widget). Facts only; no outcome is decided here (CLAUDE.md principle 2).
Moved from checks/t5d.py unchanged (2026-11-01)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from tobi508.models import Stop
from tobi508.traverse import PATH_JS, ReplayPlan, Session
from tobi508.walk import KeyboardWalk

ARRIVE_SLACK = 10  # extra Tab presses allowed when arriving at a field
BEFORE_CHARS = 1500

# ── Page reads (isolated world; `this` is the field) ─────────────────────────

_OWN_JS = """
  const doc = this.ownerDocument;
  const own = new Set([this]);
  for (const a of ['aria-controls', 'aria-owns', 'list', 'aria-describedby', 'aria-errormessage']) {
    for (const id of (this.getAttribute(a) || '').split(/\\s+/).filter(Boolean)) {
      const el = doc.getElementById(id);
      if (el) own.add(el);
    }
  }
  let mates = [];
  if (this.matches('input[type=radio]') && this.name) {
    mates = Array.from((this.form || doc).querySelectorAll('input[type=radio]'))
      .filter((r) => r.name === this.name && r.form === this.form);
  } else if (this.getAttribute('role') === 'radio') {
    const g = this.closest('[role=radiogroup]');
    if (g) { own.add(g); mates = Array.from(g.querySelectorAll('[role=radio]')); }
  }
  mates.forEach((m) => own.add(m));
  const inOwn = (n) => { for (const o of own) if (o === n || o.contains(n)) return true; return false; };
"""

# A date input's parts are focused inside its own shadow root: read the input.
_ON_HOST = (
    "function () { const h = this.getRootNode().host; "
    "const el = h && h.tagName === 'INPUT' ? h : this; return (BODY).call(el); }"
)


def _on_host(fn: str) -> str:
    return _ON_HOST.replace("BODY", fn)


FIELD_FN = _on_host(
    "function () {"
    + PATH_JS
    + _OWN_JS
    + """
  const tag = this.tagName.toLowerCase(), role = this.getAttribute('role');
  const type = (this.type || '').toLowerCase();
  const custom = !['input', 'select', 'textarea'].includes(tag);
  const value = custom
    ? (this.getAttribute('aria-valuenow') ?? this.getAttribute('aria-checked') ?? this.textContent)
    : (type === 'checkbox' ? String(this.checked)
      : type === 'radio' ? String(mates.findIndex((m) => m.checked)) : this.value);
  let label = this.getAttribute('aria-label') || '';
  if (!label && this.getAttribute('aria-labelledby')) label = this.getAttribute('aria-labelledby')
    .split(/\\s+/).map((id) => (doc.getElementById(id) || {}).textContent || '').join(' ');
  if (!label && this.labels && this.labels.length) label = this.labels[0].textContent;
  if (!label && mates.length) {
    const fs = this.closest('fieldset'); const lg = fs && fs.querySelector('legend');
    if (lg) label = lg.textContent;
  }
  // Visible text before the field in reading order, back to the start of its
  // form (or the previous heading), at most BEFORE_CHARS characters.
  const scope = this.form || this.closest('form');
  const start = scope || null;
  const texts = [];
  const tw = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
  let headingSeen = null;
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    if (this.compareDocumentPosition(n) & Node.DOCUMENT_POSITION_FOLLOWING) break;
    if (this.contains(n)) break;
    if (start && !start.contains(n)) continue;
    const p = n.parentElement;
    if (!p || !p.checkVisibility || !p.checkVisibility({ visibilityProperty: true })) continue;
    if (['SCRIPT', 'STYLE', 'OPTION'].includes(p.tagName)) continue;
    const t = n.textContent.replace(/\\s+/g, ' ').trim();
    if (!t) continue;
    if (!start && p.closest('h1,h2,h3,h4,h5,h6')) { texts.length = 0; headingSeen = true; }
    texts.push(t);
  }
  const before = texts.join(' ').slice(-BEFORE);
  const invalid = this.getAttribute('aria-invalid') === 'true' ||
    (!!this.willValidate && typeof this.checkValidity === 'function' && !this.checkValidity());
  return { tag, role, type, inputmode: this.getAttribute('inputmode'),
           maxlength: this.maxLength > 0 ? this.maxLength : null, value, label: label.trim(),
           options: mates.length || null, own: Array.from(own).map((e) => path(e)),
           before, invalid, pattern: this.getAttribute('pattern'),
           described: (this.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean)
             .map((id) => (doc.getElementById(id) || {}).textContent || '').join(' ').trim() };
}""".replace("BEFORE", str(BEFORE_CHARS))
)

# A signature of everything visible outside the field's own widget in its
# document: visible text and the number of visible dialogs.
SIG_FN = _on_host(
    "function () {"
    + _OWN_JS
    + """
  const parts = [];
  const tw = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const p = n.parentElement;
    if (!p || inOwn(p) || ['SCRIPT', 'STYLE'].includes(p.tagName)) continue;
    if (!p.checkVisibility || !p.checkVisibility({ visibilityProperty: true })) continue;
    const t = n.textContent.replace(/\\s+/g, ' ').trim();
    if (t) parts.push(t);
  }
  const dialogs = Array.from(doc.querySelectorAll('dialog[open],[role=dialog],[role=alertdialog]'))
    .filter((e) => !inOwn(e) && e.checkVisibility()).length;
  return parts.join('|') + '#' + dialogs;
}"""
)


class Field5D(BaseModel):
    n: int
    index: int  # P1 step index (-1: revealed by an earlier field, not in P1)
    path_key: str
    css_path: str | None = None
    frame_chain: list[str] = Field(default_factory=list)
    control: str
    group: str | None = None
    role: str | None = None
    name: str | None = None
    next_path: str | None = None  # the next P1 stop after the field (or group)
    next_css: str | None = None


def _fields(walk: KeyboardWalk) -> list[Field5D]:
    steps = walk.p1.steps
    out: list[Field5D] = []
    seen: set[str] = set()
    for i, s in enumerate(steps):
        st = s.stop
        if st.kind != "element" or not st.control or st.readonly or st.disabled:
            continue
        key = st.group or st.path_key
        if key in seen:
            continue
        seen.add(key)
        nxt = next(
            (
                x.stop
                for x in steps[i + 1 :]
                if x.stop.path_key != st.path_key
                and not (st.group and x.stop.group == st.group)
            ),
            None,
        )
        out.append(
            Field5D(
                n=len(out) + 1,
                index=i,
                path_key=st.path_key,
                css_path=st.css_path,
                frame_chain=st.frame_chain,
                control=st.control,
                group=st.group,
                role=st.role,
                name=st.name,
                next_path=nxt.path_key if nxt and nxt.kind == "element" else None,
                next_css=nxt.css_path if nxt and nxt.kind == "element" else None,
            )
        )
    return out


def _field_stops(walk: KeyboardWalk) -> int:
    return sum(
        1
        for p in (walk.p1, walk.p2)
        for s in p.steps
        if s.stop.kind == "element"
        and s.stop.control
        and not s.stop.readonly
        and not s.stop.disabled
    )


async def _read(s: Session) -> Stop:
    st, _ = await s.traversal.reader.read()
    return st


def _on(st: Stop, f: Field5D) -> bool:
    return st.kind == "element" and (
        st.path_key == f.path_key or bool(f.group and st.group == f.group)
    )


async def _arrive(
    s: Session, f: Field5D, limit: int, plan: ReplayPlan | None = None
) -> Stop | None:
    """Tab until focus is on the field (or one of its radio group). Presses the
    walk saw quiet (4.C spec section 2, replays) are quick, except the one the
    walk says lands on the field; arrival is checked on every press."""
    await s.traversal.resync()
    seen = plan.passes.get("Tab", []) if plan is not None else []
    where = {p: j for j, (p, _) in reversed(list(enumerate(seen)))}
    st = await _read(s)
    for _ in range(limit + 1):
        if _on(st, f):
            return st
        j = where.get(st.path_key)
        nxt = j + 1 if j is not None else None
        quick = (
            nxt is not None
            and nxt < len(seen)
            and seen[nxt][1]
            and nxt != f.index
            and seen[nxt][0] != f.path_key
        )
        step = await s.traversal.press("Tab", quick=quick)
        st = step.stop
    return None
