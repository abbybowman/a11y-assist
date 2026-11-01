# ANDI changes the page; run scanners on their own load

**Problem.** It is tempting to inject ANDI, axe-core and HTML_CodeSniffer into
the page used for the keyboard walk. ANDI adds its toolbar, shifts layout and
moves focus, which would corrupt the walk's evidence.

**What we do (planned).** The keyboard walk runs on a clean replay. Scanners
run afterwards on a separate fresh load of the same recording. ANDI is served
from `third_party/` only (`andi.install_andi_routes`), never from ssa.gov.
Scanner output is evidence for spec rows; a clean scan never means PASS.
