"""Inject the vendored ANDI 29.2.2 into a page. Never loads ANDI from ssa.gov.

ANDI's andi.js loads, at runtime and from its hard-coded host_url
(https://www.ssa.gov/accessibility/andi/): andi.css, the module script and CSS
(e.g. fandi.js), and icons. If the page has no jQuery >= 1.9.1 it also loads
jQuery 3.7.1 from ajax.googleapis.com. Context routes fulfil all of these from
third_party/ and abort anything that has no local copy, so none of these
requests reach the network. Any other www.ssa.gov request is aborted too.
Verified in tests/test_andi.py.

Injection uses an inline script tag, so a page Content-Security-Policy that
forbids inline scripts will block ANDI. No CSP bypass is enabled.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from playwright.async_api import BrowserContext, Page, Route

ANDI_HOST_URL = "https://www.ssa.gov/accessibility/andi/"
SSA_ORIGIN = "https://www.ssa.gov/"
JQUERY_URL = "https://ajax.googleapis.com/ajax/libs/jquery/"


@cache
def provenance(third_party_dir: Path) -> dict:
    return json.loads((third_party_dir / "PROVENANCE.json").read_text(encoding="utf-8"))


async def install_andi_routes(
    context: BrowserContext, third_party_dir: Path
) -> list[str]:
    """Serve ANDI and its jQuery from local files. Returns a live list of
    URLs that were aborted because no local copy exists."""
    andi_dir = (third_party_dir / "andi").resolve()
    jquery_file = third_party_dir / "jquery" / "jquery.min.js"
    jquery_version = provenance(third_party_dir)["jquery"]["version"]
    aborted: list[str] = []

    async def serve_andi(route: Route) -> None:
        url = route.request.url
        rel = url[len(ANDI_HOST_URL) :].split("?")[0].split("#")[0]
        local = (andi_dir / rel).resolve()
        if (
            url.startswith(ANDI_HOST_URL)
            and local.is_file()
            and local.is_relative_to(andi_dir)
        ):
            await route.fulfill(path=str(local))
        else:
            aborted.append(route.request.url)
            await route.abort("blockedbyclient")

    async def serve_jquery(route: Route) -> None:
        if route.request.url == f"{JQUERY_URL}{jquery_version}/jquery.min.js":
            await route.fulfill(path=str(jquery_file))
        else:
            aborted.append(route.request.url)
            await route.abort("blockedbyclient")

    # All of www.ssa.gov, so nothing ANDI references can reach ssa.gov.
    await context.route(SSA_ORIGIN + "**", serve_andi)
    await context.route(JQUERY_URL + "**", serve_jquery)
    return aborted


async def inject_andi(
    page: Page, third_party_dir: Path, timeout_ms: int = 15_000
) -> str:
    """Inject andi.js and wait for ANDI's UI. Returns the running ANDI version.

    The context must have had install_andi_routes() called first.
    """
    await page.add_script_tag(path=str(third_party_dir / "andi" / "andi.js"))
    await page.wait_for_selector("#ANDI508", state="attached", timeout=timeout_ms)
    return await page.evaluate("window.andiVersionNumber")


# ANDI's per-element analysis, read after inject_andi() (5.C; plan
# 2026-11-01-forms-5a-5c, ANDI spike). ANDI keeps it in jQuery data on each
# element it analyses (`data-andi508-index`): accName, accDesc, accGroup as
# display HTML, and alert lists. Display markup is removed (its id badges,
# such as "#cn2" before described text); an alert's message is its link's
# aria-label. Read in the main world, where ANDI's jQuery data lives.
ANDI_OUTPUT_JS = (
    "() => {"
    + """
  if (!window.jQuery || !document.querySelector('#ANDI508')) return null;
  const clean = (h) => {
    if (!h) return '';
    const t = document.createElement('template');
    t.innerHTML = String(h);
    t.content.querySelectorAll('.ANDI508-display-id').forEach((e) => e.remove());
    return (t.content.textContent || '').replace(/\\s+/g, ' ').trim();
  };
  const alerts = (a) => (a || []).map((x) => {
    const m = /aria-label='(?:danger|warning|caution): (.*?)(?: Select to Open| ')/.exec(String(x));
    return m ? m[1] : clean(x);
  });
  const seg = (n) => {
    const root = n.getRootNode();
    if (n.id && root.querySelectorAll('#' + CSS.escape(n.id)).length === 1) return { s: '#' + CSS.escape(n.id), unique: true };
    const tag = n.tagName.toLowerCase(), p = n.parentElement;
    if (!p) return { s: tag, unique: false };
    const same = Array.from(p.children).filter((c) => c.tagName === n.tagName);
    return { s: same.length > 1 ? `${tag}:nth-of-type(${same.indexOf(n) + 1})` : tag, unique: false };
  };
  const path = (n) => {
    const parts = [];
    for (let cur = n; cur && cur.nodeType === 1; cur = cur.parentElement) {
      const { s, unique } = seg(cur); parts.unshift(s);
      if (unique || !cur.parentElement) break;
    }
    return parts.join(' > ');
  };
  return Array.from(document.querySelectorAll('[data-andi508-index]')).map((el) => {
    const d = window.jQuery(el).data('andi508') || {};
    return { css: path(el), name: clean(d.accName), desc: clean(d.accDesc), group: clean(d.accGroup),
             dangers: alerts(d.dangers), warnings: alerts(d.warnings) };
  });
}"""
)


async def andi_output(page: Page) -> list[dict] | None:
    """ANDI's output per analysed element, keyed by CSS path (the walk's
    path form, top document). None when ANDI is not running on the page."""
    try:
        return await page.evaluate(ANDI_OUTPUT_JS)
    except Exception:
        return None
