# Pages that keep changing: animation is not a focus indicator

**Problem.** 4.D compares an image taken while an element has focus with one
taken after focus moves on. On a page with a slideshow or animation, pixels
and styles change between the two for reasons unrelated to focus, which could
read as an indicator (a false PASS). Such pages also never "settle", so
treating unsettled steps as unreliable sent every element to a person.

**What we do.** While the element has focus, if the page is changing (the step
did not settle, the DOM changed, or `document.getAnimations()` is not empty),
a second image and style read are taken 150 ms later. Whatever differs
between the two focused reads is noise and is left out of the comparison.
Unsettled steps are no longer unreliable by themselves. Static pages skip the
second read, which keeps 4.D near 0.2 s per element. Covered by 4.D F06.
