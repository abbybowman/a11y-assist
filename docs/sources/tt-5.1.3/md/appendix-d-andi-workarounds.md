# Appendix D: ANDI Workarounds

<!-- TT 5.1.3, printed pp. 94-96. Converted from the PDF by convert.py; the PDF is the authority. -->

On some web pages, ANDI might not run as expected. The following information is provided to diagnose the problem and possibly allow ANDI to run on these pages.

iFrame Workaround If ANDI will not run in an iframe, a possible workaround is as follows. (The following instructions are for Microsoft Edge; if necessary, try this using the developer tools in other browsers.)

1. Right click on the content contained by the iframe. Select Inspect to open DevTools.
2. Select the console tab within DevTools.
3. Access the “JavaScript Context” dropdown in DevTools to confirm you are inside the correct iFrame container as follows:

- a. Select the JavaScript Context dropdown:

- b. Open the JavaScript Context dropdown and hover the mouse pointer over entries in the dropdown until the UI on the left of the DevTools screen highlights. When the UI on the left highlights, select that item in the dropdown. The highlighting is confirmation that the iFrame hovered over in the JavaScript context dropdown is the iFrame container in which you should paste the ANDI code:

4. Copy the ANDI favelet code from the browser and paste into the iFrame container at the “>” prompt at the bottom of the DevTools Console. Select “ENTER” to start the ANDI tool within the iFrame container:

5. ANDI should run normally within the iFrame container.

Other Issues Some sites have content security policy (CSP) enhancements to prevent outside scripts from executing on the page to prevent phishing and other security threats. There may also be scripting restrictions. These may interfere with ANDI running on these pages.

SSA provides possible workarounds under ANDI's FAQ in the "Why won't ANDI work on this page?" section at https://www.ssa.gov/accessibility/andi/help/faq.html#wontLaunch.

**Note:** Check with your IT Department to obtain approval before trying these workarounds. Be sure to re-enable CSP

and other restrictions after testing.
