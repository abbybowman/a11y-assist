# Shadow roots: `contains()` stops at the boundary

**Problem.** 4.A asks whether a pointer target is "reached": a stop, inside a
stop, or around one. `a.contains(b)` is false when `b` is in `a`'s shadow
root, and `document.querySelector("#host #btn")` finds nothing for a path
that crosses a shadow boundary (the walk writes it as a lone space). The
first version fell back to the host and called the shadow button on
`no_trap.html` unreachable, sending a working page to a person.

**What we do.** `t4a._COMMON_JS`: `find()` resolves a path part by part
through each `shadowRoot`; `deepContains()` walks up through `parentNode`
or `host`. Covered by `test_fixtures_4a.py::test_shadow_and_frame_stops_are_reached`.
Any new scan that matches the walk's paths should reuse these helpers and
`traverse.PATH_JS`, which builds the walk's own paths.
