# Widget items: roving tabindex and aria-activedescendant

**Why they need arrow keys.** Items inside menubars, tab lists, listboxes and
grids get focus from arrow keys, not Tab, so the shared walk reaches only one
item per widget. With aria-activedescendant, DOM focus stays on the container
and the "focused" item is the one the attribute names (WAI-ARIA 1.2: it "is
treated as having keyboard focus"; the author styles it). 4.D's widget pass W
arrows through up to 5 items.

**Lessons.**
- Mask the *next subject's* box (the next active item), not the element with
  DOM focus: for an active-descendant listbox that is the whole list, which
  masked almost everything.
- At the end of a widget the arrow stops moving, so the last item never gets
  its "after" read; press the opposite arrow once.
- Try ArrowDown, then ArrowRight if nothing moved, instead of guessing the
  orientation from the role.
