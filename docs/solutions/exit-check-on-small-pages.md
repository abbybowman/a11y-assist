# An exit check must accept reaching the end of the page

**Problem.** Spec 1.5.0 calls a probe an exit when it reaches a stop outside
the trap and the next 3 presses do not return to it. On a 3-element page,
3 more Tabs go past the end (OUT), wrap to the top and land on the trap again,
so a real exit (F16: Escape, then Tab, leaves a textarea) read as a FAIL.

**What we do.** Reaching OUT during the check confirms the exit: traversal got
past the rest of the page. OUT before any outside stop still does not count.
`t4c.Collector.probe`; covered by the F16 outcome test.

**Second lesson (ACT b92b5214).** "Returns to a trap member" is also wrong as
the test: after Ctrl+M switches the trap off, Shift+Tab walks back through the
former trap's buttons, which are now free. The check now asks whether the trap
*happens again* (stuck, or looping only on its own stops) within
2 x trap size + 3 presses.
