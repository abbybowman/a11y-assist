"""Vendor W3C ACT test cases and DHS's Trusted Tester results on them.

Run deliberately, then review the diff:

    uv run python -I tests/fixtures/act/sync_act.py

Tests never fetch from the network; they serve the files this script saved.
Pages are saved byte for byte and never edited. They load assets by absolute
path (/WAI/content-assets/...), so they are stored under that same path here
and this folder is served as the web root.

Expected outcomes are ours (from docs/rules/4c-build-tasks.md) and live only in
manifest.json, never in a page. If a case's testcaseId changes, the script stops
so the change is reviewed instead of silently accepted.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

HERE = Path(__file__).resolve().parent
TESTCASES_URL = "https://www.w3.org/WAI/content-assets/wcag-act-rules/testcases.json"
DHS_URL = (
    "https://raw.githubusercontent.com/Section508Coordinators/act-tt/main/"
    "act-trusted-tester.json"
)
ALLOWED_HOST = "www.w3.org"

# TT test -> ACT rule IDs.
RULES = {"4.C": ["a1b64e", "ebe86a", "80af7b"], "4.D": ["oj04fd"]}
# Unapproved near-copies of approved cases (docs/rules/4d-build-tasks.md).
SKIP = {"8f296b7a", "eb4f387b"}

# Our expected outcome per case (first 8 hex of testcaseId), from the build
# tasks table. A case missing here stops the sync.
EXPECTED = {
    "4.C": {
        "96eb4b26": "PASS",
        "d26e3cbd": "PASS",
        "fb76f71a": "PASS",
        "4b93a866": "DNA",  # OPEN O4: DHS gave PASS
        "dcf917e0": "PASS",
        "f5ea9fd3": "FAIL",
        "d2f5325f": "FAIL",
        "0ec0e93e": "FAIL",
        "16dddd8a": "DNA",
        "6e3dcc2f": "DNA",
        "9d47dcc6": "DNA",
        "30ffb299": "DNA",
        "ab24c77e": "PASS",
        "e3902f01": "PASS",
        "b92b5214": "PASS",
        "7dcc4ae0": "FAIL",
        "8fba3918": "FAIL",
        "62fd24e7": "FAIL",
        "b20beca9": "PASS",
    },
    # docs/rules/4d-build-tasks.md
    "4.D": {
        "52be6331": "PASS",
        "95cf4fdf": "PASS",
        "b44aa294": "PASS",
        "dd9628d8": "PASS",
        "f1c9efb4": "FAIL",
        "90789ad8": "DNA",
        "b12f1f45": "DNA",
    },
}

EARL = {
    "earl:passed": "PASS",
    "earl:failed": "FAIL",
    "earl:inapplicable": "DNA",
    "earl:untested": "NOT_TESTED",
    "earl:cantTell": "NEEDS_REVIEW",
    "passed": "PASS",
    "failed": "FAIL",
    "inapplicable": "DNA",
}

# Assets only: src= on any element, and href= on <link>. Ordinary <a href>
# links are navigation, not assets, and are never fetched.
_ASSET = re.compile(
    r"""(?:\bsrc\s*=\s*["']([^"'#]+)["']|<link\b[^>]*\bhref\s*=\s*["']([^"'#]+)["'])""",
    re.I,
)


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - fixed hosts
        return r.read()


def save(url: str) -> Path:
    """Save a w3.org file under its URL path; return the local path."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise SystemExit(f"refusing to fetch {url}: only https://{ALLOWED_HOST}")
    local = HERE / parsed.path.lstrip("/")
    if HERE not in local.resolve().parents:
        raise SystemExit(f"refusing path outside the fixture folder: {url}")
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(fetch(url))
    return local


def assets(page_url: str, html: str) -> list[str]:
    """Same-host assets a page references (scripts, styles, images, frames)."""
    out = []
    for groups in _ASSET.findall(html):
        ref = next(g for g in groups if g)
        url = urljoin(page_url, ref.strip())
        path = urlparse(url).path
        if urlparse(url).hostname == ALLOWED_HOST and (
            "/test-assets/" in path or not path.endswith(".html")
        ):
            out.append(url)
    return out


def main() -> None:
    raw = fetch(TESTCASES_URL)
    testcases = json.loads(raw)
    dhs = json.loads(fetch(DHS_URL))
    dhs_by_hash: dict[str, set[str]] = {}
    for a in dhs["assertedThat"]:
        h = a["subject"]["source"].rsplit("/", 1)[-1].removesuffix(".html")
        dhs_by_hash.setdefault(h, set()).add(EARL[a["result"]["outcome"]])

    old = {}
    manifest_path = HERE / "manifest.json"
    if manifest_path.exists():
        old = {
            c["id"]: c["testcaseId"]
            for c in json.loads(manifest_path.read_text())["cases"]
        }

    cases: dict[str, dict] = {}
    for tt, rule_ids in RULES.items():
        for c in testcases["testcases"]:
            if c["ruleId"] not in rule_ids:
                continue
            tid = c["testcaseId"]
            short = tid[:8]
            if short in SKIP:
                continue
            entry = cases.setdefault(
                tid,
                {
                    "id": short,
                    "testcaseId": tid,
                    "tt_test": tt,
                    "examples": [],
                    "act_expected": {},
                    "approved": {},
                    "url": c["url"],
                },
            )
            entry["examples"].append(f"{c['ruleId']} {c['testcaseTitle']}")
            entry["act_expected"][c["ruleId"]] = EARL[c["expected"]]
            entry["approved"][c["ruleId"]] = bool(
                c.get("approved") or c.get("isApproved")
            )

    changed = [
        s
        for s, t in old.items()
        if s in {c["id"] for c in cases.values()} and t not in cases
    ]
    if changed:
        raise SystemExit(f"testcaseId changed for {changed}; review before syncing")

    files: dict[str, str] = {}
    for entry in cases.values():
        tt, short = entry["tt_test"], entry["id"]
        if short not in EXPECTED[tt]:
            raise SystemExit(f"no expected outcome for {short}; add it to EXPECTED")
        dhs_outcomes = dhs_by_hash.get(entry["testcaseId"], set())
        if len(dhs_outcomes) > 1:
            raise SystemExit(f"DHS gave {short} conflicting outcomes {dhs_outcomes}")
        entry["dhs_tt51"] = next(iter(dhs_outcomes), None)
        entry["expected"] = EXPECTED[tt][short]
        page = save(entry["url"])
        entry["path"] = page.relative_to(HERE).as_posix()
        for url in assets(entry["url"], page.read_text("utf-8")):
            path = save(url)
            files[path.relative_to(HERE).as_posix()] = ""
        files[entry["path"]] = ""
        entry["examples"].sort()

    for rel in files:
        files[rel] = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()

    manifest = {
        "source": TESTCASES_URL,
        "testcases_sha256": hashlib.sha256(raw).hexdigest(),
        "dhs_source": DHS_URL,
        "license": testcases.get("license"),
        "cases": sorted(cases.values(), key=lambda e: e["id"]),
        "files": dict(sorted(files.items())),
    }
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{len(cases)} cases, {len(files)} files", file=sys.stderr)


if __name__ == "__main__":
    main()
