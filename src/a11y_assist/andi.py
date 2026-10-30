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
