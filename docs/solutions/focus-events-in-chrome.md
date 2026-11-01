# Focus events in Chrome: what the log does and doesn't show

**Blur inside a focus handler.** When an element calls `this.blur()` in its
own focus handler (F55), Chrome fires no `focusin` for it. The log shows only
the previous element's `focusout`, whose `relatedTarget` names the element
focus was going to. 4.E takes the target from there (`t4e.classify`).

**What the log records** (`traverse.INIT_JS`, every frame, before page
scripts): type, time, tag, id, `isTrusted`, a short element path, and for
`focusout` the `relatedTarget` path and whether it is inside the element
losing focus (a widget handing focus to its own item). Untrusted (synthetic)
events make a step unreliable.

**Fixture trap: `id="close"`.** An element id becomes a global name, but
built-ins win: `close` is `window.close`, so `close.focus()` silently does
nothing. Use `document.getElementById(...)` in fixture scripts.
