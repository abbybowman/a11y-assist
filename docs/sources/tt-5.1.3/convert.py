"""Convert the TT 5.1.3 PDF into Markdown (one file per part) and tt.json.

A one-time conversion, kept so it can be re-run and checked. The PDF stays the
authority; this is a faithful text copy in a predictable shape:

  md/*.md   the whole document, split by part (front matter, sections 1-20,
            appendices), as Markdown: headings, lists, test-condition tables.
            Layout tables (change log, quick reference, mapping) are kept as
            fenced text blocks, exactly as laid out.
  tt.json   the 63 test conditions: ID, name, condition, section, pages,
            requirements (from Appendix A), and each test's blocks (Identify
            Content, Applicability, How to Test, Evaluate Results, notes) as
            Markdown, with WCAG links from W3C's wcag.json.

Run (needs poppler's pdftotext; outputs are committed, so tests do not):

  python -I docs/sources/tt-5.1.3/convert.py /path/to/wcag22.json

The script fails unless every word of the PDF body (headers and footers
removed) appears in the Markdown in the same order, with nothing added.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = HERE.parent / "Trusted Tester Test Process v5.1.3.pdf"
WCAG_JSON_URL = "https://www.w3.org/WAI/WCAG22/wcag.json"
UNDERSTANDING = "https://www.w3.org/WAI/WCAG22/Understanding/{}.html"
WCAG20_CONFORMANCE = "https://www.w3.org/TR/WCAG20/#conformance-reqs"

# Parts of the document, in order: (file stem, heading as printed, level).
PARTS = [
    ("00-about", "About This Document"),
    ("00-test-environment", "Test Environment"),
    ("00-conformance-reporting", "Conformance Reporting Requirements"),
    ("00-section-508-conformance-tests", "Section 508 Conformance Tests"),
    (
        "01-conforming-alternate-version",
        "1. Conforming Alternate Version (CAV) and Non-Interference",
    ),
    ("02-auto-playing-and-auto-updating", "2. Auto-Playing and Auto-Updating Content"),
    ("03-flashing", "3. Flashing"),
    ("04-keyboard-access-and-focus", "4. Keyboard Access and Focus"),
    ("05-forms", "5. Forms"),
    ("06-links", "6. Links"),
    ("07-images", "7. Images"),
    ("08-adjustable-time-limits", "8. Adjustable Time Limits"),
    ("09-repetitive-content", "9. Repetitive Content"),
    ("10-content-structure", "10. Content Structure"),
    ("11-language", "11. Language"),
    ("12-page-titles-frames-iframes", "12. Page Titles, Frames, and iFrames"),
    (
        "13-sensory-characteristics-and-contrast",
        "13. Sensory Characteristics and Contrast",
    ),
    ("14-tables", "14. Tables"),
    ("15-css-positioning", "15. CSS Positioning"),
    (
        "16-prerecorded-audio-video-animations",
        "16. Pre-Recorded Audio-Only, Video-Only, and Animations",
    ),
    ("17-synchronized-media", "17. Synchronized Media"),
    ("18-resize-text", "18. Resize Text"),
    ("19-multiple-ways", "19. Multiple Ways"),
    ("20-parsing", "20. Parsing"),
    ("appendix-a-test-process-mapping", "Appendix A: Test Process Mapping"),
    ("appendix-b-change-log", "Appendix B: Document Change Log"),
    ("appendix-c-quick-reference", "Appendix C: Test Process Quick Reference"),
    ("appendix-d-andi-workarounds", "Appendix D: ANDI Workarounds"),
]
# Parts whose tables are layout tables, kept as fenced text.
FENCED_PARTS = {
    "appendix-a-test-process-mapping",
    "appendix-b-change-log",
    "appendix-c-quick-reference",
}
# Sub-headings from the table of contents (pp. i-ii), plus the tool names
# under Testing Tools.
SUBHEADINGS = {
    "Who Should Use this Document",
    "Differences from Previous Versions (5.0 to 5.1.2)",
    "Harmonized Baseline Alignment",
    "How this Document is Structured",
    "Web Content Tests Only",
    "Testing Order",
    "Issues Not Covered in This Test Process",
    "The Rationale for Each Test",
    "Testing Tools",
    "ANDI",
    "Colour Contrast Analyzer",
    "Operating Systems",
    "Browsers",
    "Test to Section 508/WCAG Requirement and Baseline Test (cross-reference table)",
    "Section 508/WCAG Requirement to Trusted Tester Test and Baseline Test (cross-reference table)",
    "Quick Reference with Test Conditions",
    "One-Page Quick Reference – Test Names Only",
}
LABELS = re.compile(
    r"^(Applicability|How to Test|Evaluate Results|Notes?|Tips?|Testing Tips|"
    r"Test Instructions|Instructions)\s*(?::\s*(.*)|$)"
)
MARKER = re.compile(r"^(\d{1,2}\.|[a-z]\.|[ivx]{1,4}\.|•|o|▪|➢|-)(\s+)(?=\S)")
TABLE_HEAD = re.compile(r"^\s*Test Name\s+Test ID\s+Test Condition\s*$")
TEST_ID = re.compile(r"^\d{1,2}\.[A-Z]$")
CHECK = re.compile(r"^(?:.{1,60}? – )?Check (\S+)( \(Obsolete\))?$")


def norm(s: str) -> str:
    """Alphanumerics only: the comparison key for 'no text lost or added'."""
    return re.sub(r"[^0-9A-Za-z]", "", s)


def strip_marker(line: str) -> str:
    """Drop a list marker (o, •, 1., a.) so both sides normalize the same."""
    return MARKER.sub("", line.strip(), count=1)


# ── Pages: drop running headers and footers ─────────────────────────────────


def read_pages() -> list[tuple[int, list[str]]]:
    txt = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    raw = txt.split("\f")
    titles = Counter()
    for p in raw:
        nb = [line for line in p.split("\n") if line.strip()]
        if nb:
            m = re.match(r"^(.*?\S)?\s*(\d+|[ivx]+)\s*$", nb[-1])
            if m and m.group(1):
                titles[m.group(1).strip()] += 1
    out = []
    for index, p in enumerate(raw, start=1):
        lines = p.split("\n")
        # Running header: the first two non-blank lines (DHS, Directorate).
        body, seen = [], 0
        for line in lines:
            if seen < 2 and line.strip():
                if (
                    "Department of Homeland Security" in line
                    or "Customer Experience" in line
                ):
                    seen += 1
                    continue
            body.append(line)
        while body and not body[-1].strip():
            body.pop()
        # Footer: "<running title>   <page>", or the title then the number on
        # its own line, often preceded by "Section 508 Conformance Tests".
        if body and re.match(r"^\s*(\d+|[ivx]+)\s*$", body[-1]):
            body.pop()
            while body and not body[-1].strip():
                body.pop()
            if body and body[-1].strip() in titles:
                body.pop()
        elif body:
            m = re.match(r"^(.*?\S)\s{2,}(\d+|[ivx]+)\s*$", body[-1])
            if m and m.group(1).strip() in titles:
                body.pop()
        while body and not body[-1].strip():
            body.pop()
        if body and body[-1].strip() == "Section 508 Conformance Tests" and index > 9:
            body.pop()
        out.append((index - 3, body))  # printed page = PDF page - 3
    return out


# ── Markdown ─────────────────────────────────────────────────────────────────


def table_rows(lines: list[str]) -> tuple[list[dict], int]:
    """Parse a 'Test Name | Test ID | Test Condition' table starting at
    lines[0] (the header). Returns (rows, lines consumed)."""
    head = lines[0]
    c_id, c_cond = head.index("Test ID"), head.index("Test Condition")
    rows: list[dict] = []
    i = 1
    while i < len(lines):
        line = lines[i]
        if not line.strip() or LABELS.match(line.strip()):
            break
        # A row starts where a test ID sits near the Test ID column; text can
        # start a column or two off its header.
        m = re.match(r"^(.*?)\s+(\d{1,2}\.[A-Z])(\s+(\S.*))?$", line)
        if m and abs(m.start(2) - c_id) <= 3:
            name = m.group(1).strip()
            cond = (m.group(4) or "").strip()
            rows.append(
                {"name": [name], "id": m.group(2), "condition": [cond] if cond else []}
            )
        elif rows:
            lead = len(line) - len(line.lstrip())
            if lead >= c_cond - 3:
                rows[-1]["condition"].append(line.strip())
            else:
                gap = re.search(r"\s{3,}", line.strip())
                if gap and lead < c_id - 2:
                    name, cond = line.strip()[: gap.start()], line.strip()[gap.end() :]
                    rows[-1]["name"].append(name)
                    rows[-1]["condition"].append(cond)
                else:
                    rows[-1]["name"].append(line.strip())
        else:
            break
        i += 1
    for r in rows:
        r["name"] = join_fragments(r["name"])
        r["condition"] = " ".join(r["condition"]).strip()
    return rows, i


def join_fragments(parts: list[str]) -> str:
    out = ""
    for p in parts:
        if not out:
            out = p
        elif out.endswith("-"):
            out += p.lstrip()
        else:
            out += " " + p
    return out


def is_layout_row(line: str) -> bool:
    return bool(re.search(r"\S\s{3,}\S", strip_marker(line)))


def to_markdown(lines: list[str], fenced: bool) -> tuple[str, list[dict]]:
    """Lines of one part -> Markdown. Returns (markdown, condition tables)."""
    out: list[str] = []
    tables: list[dict] = []
    para: list[str] = []
    stack: list[int] = []  # list indent columns

    def flush():
        if para:
            out.append(join_fragments(para))
            para.clear()

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            stack.clear()
            if out and out[-1] != "":
                out.append("")
            i += 1
            continue
        if TABLE_HEAD.match(line):
            flush()
            rows, used = table_rows(lines[i:])
            tables.append({"rows": rows, "source": lines[i : i + used]})
            out += [
                "",
                "| Test Name | Test ID | Test Condition |",
                "| --- | --- | --- |",
            ]
            out += [f"| {r['name']} | {r['id']} | {r['condition']} |" for r in rows]
            out.append("")
            i += used
            continue
        if s == "Applicable Standards":
            # A two-column table (requirement text | baseline): kept as laid
            # out, up to the next test, Identify Content or subgroup heading.
            flush()
            j = i + 1
            block = []
            while j < n:
                t = lines[j].strip()
                nt = lines[j + 1].strip() if j + 1 < n else ""
                if (
                    CHECK.match(t)
                    or t == "Identify Content"
                    or (nt == "Identify Content" and t and len(t) < 60)
                ):
                    break
                block.append(lines[j].rstrip())
                j += 1
            while block and not block[-1].strip():
                block.pop()
            ind = min(len(b) - len(b.lstrip()) for b in block if b.strip())
            out += ["", "**Applicable Standards**", "", "```text"]
            out += [b[ind:] for b in block] + ["```", ""]
            i = j
            continue
        if fenced and is_layout_row(line):
            flush()
            j = i
            block = []
            while j < n and lines[j].strip():
                block.append(lines[j].rstrip())
                j += 1
            ind = min(len(b) - len(b.lstrip()) for b in block)
            out += ["", "```text", *[b[ind:] for b in block], "```", ""]
            i = j
            continue
        if s in SUBHEADINGS:
            flush()
            out += ["", f"## {s}", ""]
            i += 1
            continue
        if s in ("AND", "OR"):
            flush()  # a connector between list items, on its own line
            out += ["", s, ""]
            i += 1
            continue
        if CHECK.match(s):
            flush()
            out += ["", f"### {s}", ""]
            i += 1
            continue
        if s == "Identify Content":
            flush()
            out += ["", "#### Identify Content", ""]
            i += 1
            continue
        nxt = lines[i + 1].strip() if i + 1 < n else ""
        if nxt == "Identify Content" and len(s) < 60 and not s.endswith((".", ":")):
            flush()
            out += ["", f"### {s}", ""]  # a subgroup, e.g. "Keyboard Access", "Focus"
            i += 1
            continue
        m = LABELS.match(s)
        if m and line[: len(line) - len(line.lstrip())] == "":
            flush()
            stack.clear()
            colon = ":" if ":" in s else ""
            out += [
                "",
                f"**{m.group(1)}{colon}**" + (f" {m.group(2)}" if m.group(2) else ""),
                "",
            ]
            i += 1
            continue
        mk = MARKER.match(s)
        if mk and not (mk.group(1) == "o" and not s[1:2].isspace()):
            flush()
            col = len(line) - len(line.lstrip())
            while stack and stack[-1] > col:
                stack.pop()
            if not stack or stack[-1] < col:
                stack.append(col)
            depth = len(stack) - 1
            marker = mk.group(1)
            text = s[mk.end() :]
            if marker in ("•", "o", "▪", "➢", "-"):
                item = f"- {text}"
            elif re.match(r"^\d", marker):
                item = f"{marker} {text}"
            else:
                item = f"- {marker} {text}"  # a. / i. are not Markdown markers
            para.append("    " * depth + item)
            i += 1
            continue
        para.append(s if not para else s)
        i += 1
    flush()
    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md, tables


def md_stream(md: str) -> str:
    """Normalize Markdown back to the comparison key."""
    keep = []
    for line in md.split("\n"):
        t = line.strip()
        if (
            t.startswith("```")
            or re.match(r"^\|\s*-", t)
            or t == "| Test Name | Test ID | Test Condition |"
        ):
            continue
        t = re.sub(r"^#+\s*", "", t)
        t = re.sub(r"^- (?=[a-z]\. |[ivx]{1,4}\. )", "", t)
        t = strip_marker(t) if not t.startswith("|") else t
        keep.append(t)
    return norm("".join(keep))


def src_stream(lines: list[str]) -> str:
    return norm("".join(strip_marker(line) for line in lines))


# ── Build ────────────────────────────────────────────────────────────────────


def check_part(stem: str, lines: list[str], md: str) -> list[str]:
    """Same text, same order. Condition tables are rendered row by row (cells
    joined), so their text is compared as characters."""
    _, tables = to_markdown(lines, fenced=stem in FENCED_PARTS)
    src_lines, table_src = [], []
    k = 0
    while k < len(lines):
        if TABLE_HEAD.match(lines[k]):
            _, used = table_rows(lines[k:])
            table_src += lines[k : k + used]
            k += used
            continue
        src_lines.append(lines[k])
        k += 1
    md_no_tables = "\n".join(ln for ln in md.split("\n") if not ln.startswith("| "))
    out = []
    a, b = src_stream(src_lines), md_stream(md_no_tables)
    if a != b:
        at = next(
            (x for x in range(min(len(a), len(b))) if a[x] != b[x]), min(len(a), len(b))
        )
        out.append(
            f"{stem}: text differs at {at}: src …{a[max(0, at - 40) : at + 40]}… md …{b[max(0, at - 40) : at + 40]}…"
        )
    rows = [
        ln
        for ln in md.split("\n")
        if ln.startswith("| ") and not ln.startswith("| Test Name |")
    ]
    got = Counter(norm("".join(rows)))
    want = Counter(norm("".join(table_src))) - Counter(
        norm("Test Name Test ID Test Condition" * len(tables))
    )
    if got != want:
        out.append(
            f"{stem}: table text differs: extra {got - want}, missing {want - got}"
        )
    return out


def split_parts(pages):
    """Assign body lines to parts by their printed headings."""
    flat = [(pg, line) for pg, body in pages for line in body]
    # The table of contents (pages i-ii) and cover are skipped.
    start = next(
        k
        for k, (pg, line) in enumerate(flat)
        if pg == 1 and line.strip() == "About This Document"
    )
    heads = []
    want = iter(PARTS)
    cur = next(want)
    for k in range(start, len(flat)):
        text = flat[k][1].strip()
        if (
            cur
            and text.replace(". ", ".").replace(".", ". ", 1)
            == cur[1].replace(". ", ".").replace(".", ". ", 1)
            or (cur and text == cur[1])
        ):
            heads.append((cur, k))
            cur = next(want, None)
    assert len(heads) == len(PARTS), [h[0][0] for h in heads]
    parts = []
    for idx, ((stem, title), k) in enumerate(heads):
        end = heads[idx + 1][1] if idx + 1 < len(heads) else len(flat)
        chunk = flat[k + 1 : end]
        parts.append((stem, title, chunk))
    return parts


def appendix_a(lines: list[str]) -> dict[str, dict]:
    """Test ID -> {name, requirements, baseline} from Appendix A's first table."""
    out: dict[str, dict] = {}
    cols = None
    cur = None
    for line in lines:
        if "Section 508/WCAG Requirement to Trusted Tester Test" in line:
            break
        if re.match(
            r"^\s*Test ID\s+Test Name\s+Section 508 / WCAG Requirement\s+Baseline Test",
            line,
        ):
            cols = (
                line.index("Test Name"),
                line.index("Section 508"),
                line.index("Baseline Test"),
            )
            continue
        if cols is None or not line.strip():
            continue
        a, b, c = cols
        tid, name, req, base = (
            line[:a].strip(),
            line[a:b].strip(),
            line[b:c].strip(),
            line[c:].strip(),
        )
        if TEST_ID.match(tid):
            cur = out[tid] = {
                "name": [name],
                "requirements": [req] if req else [],
                "baseline": [base] if base else [],
            }
        elif cur is not None:
            if name:
                cur["name"].append(name)
            if req:
                cur["requirements"].append(req)
            if base:
                cur["baseline"].append(base)
    for v in out.values():
        v["name"] = re.sub(r"-\s+", "-", join_fragments(v["name"]))
    return out


def appendix_c(lines: list[str]) -> dict[str, dict]:
    """Test ID -> {name, condition} from Appendix C's quick reference table."""
    out: dict[str, dict] = {}
    cols = None
    cur = None
    for line in lines:
        if line.strip().startswith("One-Page Quick Reference"):
            break
        if re.match(r"^\s*Test ID\s+Test Name\s+Test Condition\s*$", line):
            cols = (line.index("Test Name"), line.index("Test Condition"))
            continue
        if cols is None or not line.strip():
            continue
        a, b = cols
        tid, name, cond = line[:a].strip(), line[a:b].strip(), line[b:].strip()
        if not tid and not name and line[: b - 2].strip() == "":
            cond = line.strip()
        if TEST_ID.match(tid):
            cur = out[tid] = {"name": [name], "condition": [cond] if cond else []}
        elif cur is not None:
            if name:
                cur["name"].append(name)
            if cond:
                cur["condition"].append(cond)
    for v in out.values():
        v["name"] = re.sub(r"-\s+", "-", join_fragments(v["name"]))
        v["condition"] = " ".join(v["condition"])
    return out


def requirement(label: str, scs: dict) -> dict:
    m = re.match(r"^(\d\.\d\.\d+)\s+(.*)$", label)
    if m:
        sc = scs.get(m.group(1))
        level = sc["level"] if sc else None
        note = None
        if m.group(1) == "4.1.1":
            level, note = (
                "A",
                "Level A in WCAG 2.0; obsolete and removed in WCAG 2.2 (W3C wcag.json).",
            )
        return {
            "id": m.group(1),
            "label": label,
            "kind": "wcag",
            "level": level,
            "handle": sc["handle"] if sc else None,
            "understanding_url": UNDERSTANDING.format(sc["id"]) if sc else None,
            **({"note": note} if note else {}),
        }
    m = re.match(r"^(50\d\.[\d.]+)\s+(.*)$", label)
    if m:
        return {"id": m.group(1), "label": label, "kind": "section508"}
    m = re.match(r"^(Con\.\d)\s+(.*)$", label)
    if m:
        return {
            "id": m.group(1),
            "label": label,
            "kind": "wcag-conformance",
            "url": WCAG20_CONFORMANCE,
        }
    raise ValueError(f"unknown requirement {label!r}")


def merge_requirements(reqs: list[str]) -> list[str]:
    """Join wrapped requirement labels ('503.4 User Controls ... and Audio' +
    'Description')."""
    out: list[str] = []
    for r in reqs:
        if out and not re.match(r"^(\d\.\d\.\d+|50\d\.|Con\.\d)", r):
            out[-1] += " " + r
        else:
            out.append(r)
    return out


def blocks(md: str) -> dict[str, str]:
    """Split one test's Markdown into its labelled blocks."""
    out: dict[str, list[str]] = {"condition_table": []}
    key = "condition_table"
    for line in md.split("\n"):
        m = re.match(
            r"^\*\*(Applicability|How to Test|Evaluate Results|Notes?|Tips?|Testing Tips|Test Instructions|Instructions):?\*\*\s*(.*)$",
            line,
        )
        if m:
            key = {"Note": "notes", "Notes": "notes"}.get(
                m.group(1), m.group(1).lower().replace(" ", "_")
            )
            out.setdefault(key, [])
            if m.group(2):
                out[key].append(m.group(2))
            continue
        out.setdefault(key, []).append(line)
    return {k: "\n".join(v).strip() for k, v in out.items() if "\n".join(v).strip()}


def main(wcag_json: str) -> None:
    pages = read_pages()
    parts = split_parts(pages)
    wcag_raw = Path(wcag_json).read_bytes()
    wcag = json.loads(wcag_raw)
    scs = {
        s["num"]: s
        for p in wcag["principles"]
        for g in p["guidelines"]
        for s in g["successcriteria"]
    }
    (HERE / "md").mkdir(exist_ok=True)
    tests: dict[str, dict] = {}
    mapping: dict[str, dict] = {}
    quick: dict[str, dict] = {}
    files = []
    problems = []
    for stem, title, chunk in parts:
        lines = [line for _, line in chunk]
        pgs = [pg for pg, _ in chunk] or [0]
        md, tables = to_markdown(lines, fenced=stem in FENCED_PARTS)
        doc = f"# {title}\n\n<!-- TT 5.1.3, printed pp. {min(pgs)}-{max(pgs)}. Converted from the PDF by convert.py; the PDF is the authority. -->\n\n{md}"
        (HERE / "md" / f"{stem}.md").write_text(doc, encoding="utf-8")
        files.append(
            {"file": f"md/{stem}.md", "title": title, "pages": [min(pgs), max(pgs)]}
        )
        problems += check_part(stem, lines, md)
        if stem == "appendix-a-test-process-mapping":
            mapping = appendix_a(lines)
        if stem == "appendix-c-quick-reference":
            quick = appendix_c(lines)
        # Tests in this part.
        if re.match(r"^\d\d-", stem) and not stem.startswith("00"):
            num = int(stem[:2])
            sec_md = md
            # Split at test tables: each test runs from its "### Check" (or
            # table) to the next one.
            pieces = re.split(r"\n(?=### (?:.{1,60}? – )?Check )", "\n" + sec_md)
            identify = ""
            for piece in pieces:
                ic = re.search(
                    r"#### Identify Content\n(.*?)(?=\n### |\Z)", piece, re.S
                )
                ids = re.findall(r"^\| [^|]* \| (\d{1,2}\.[A-Z]) \|", piece, re.M)
                if not ids:
                    if ic:
                        identify = ic.group(1).strip()
                    continue
                head = re.match(
                    r"### ((?:.{1,60}? – )?Check \S+(?: \(Obsolete\))?)", piece
                )
                body = piece
                if ic and ids:
                    # An Identify Content block after this test belongs to the next.
                    pre, _, post = piece.partition("#### Identify Content")
                    body = pre
                for row in [r for t in tables for r in t["rows"] if r["id"] in ids]:
                    b = blocks(re.sub(r"^### .*\n", "", body.strip()))
                    tests[row["id"]] = {
                        "id": row["id"],
                        "check_heading": head.group(1) if head else None,
                        "table_name": row["name"],
                        "condition": row["condition"],
                        "section": {
                            "number": num,
                            "title": title,
                            "file": f"md/{stem}.md",
                        },
                        "identify_content": identify,
                        **{k: v for k, v in b.items() if k != "condition_table"},
                        "markdown": body.strip(),
                    }
                if ic:
                    identify = (
                        re.search(
                            r"#### Identify Content\n(.*?)(?=\n### |\Z)", piece, re.S
                        )
                        .group(1)
                        .strip()
                    )
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    assert len(mapping) == 62, len(mapping)  # Appendix A omits 6.B (removed)
    out_tests = []
    for tid in sorted(
        set(mapping) | set(quick), key=lambda x: (int(x.split(".")[0]), x)
    ):
        m, q, t = mapping.get(tid), quick.get(tid), tests.get(tid)
        if m is None:
            # 6.B: only in the Appendix C quick reference; the change log says
            # "6.B has been removed" (Appendix B).
            out_tests.append(
                {
                    "id": tid,
                    "name": q["name"],
                    "status": "removed",
                    "status_basis": "Listed only in Appendix C; Appendix B says it has been removed.",
                    "condition": q["condition"],
                    "requirements": [],
                }
            )
            continue
        if t is None:
            problems.append(f"{tid}: in Appendix A but no test block found")
            continue
        status, basis = "active", None
        if (
            "(Obsolete)" in (t["check_heading"] or "")
            or "no longer required" in t["markdown"]
        ):
            status, basis = (
                "obsolete",
                "Its section says it is no longer required (Baseline 3.1).",
            )
        qc = q["condition"] if q else None
        out_tests.append(
            {
                "id": tid,
                "name": m["name"],
                "status": status,
                **({"status_basis": basis} if basis else {}),
                "condition": t["condition"],
                **(
                    {"quick_reference_condition": qc}
                    if qc and norm(qc) != norm(t["condition"])
                    else {}
                ),
                "section": t["section"],
                "requirements": [
                    requirement(r, scs) for r in merge_requirements(m["requirements"])
                ],
                "baseline_test": join_fragments(m["baseline"]),
                # True only where the test's own text says to record NOT TESTED
                # (PDF p. 6); a mention of another test's result does not count.
                "not_tested_named": bool(
                    re.search(r"recorded as NOT TESTED", t["condition"] + t["markdown"])
                ),
                "identify_content": t["identify_content"],
                **{
                    k: t[k]
                    for k in (
                        "applicability",
                        "how_to_test",
                        "evaluate_results",
                        "notes",
                        "tips",
                        "testing_tips",
                    )
                    if k in t
                },
                "markdown": t["markdown"],
            }
        )
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    pdf_sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
    version = subprocess.run(
        ["pdftotext", "-v"], capture_output=True, text=True
    ).stderr.split("\n")[0]
    data = {
        "document": "Section 508 Conformance Test Process for Web (Trusted Tester)",
        "version": "5.1.3",
        "date": "April 2024",
        "publisher": "U.S. Department of Homeland Security, Customer Experience Directorate",
        "source_pdf_sha256": pdf_sha,
        "converted_with": f"convert.py, {version} -layout",
        "wcag_source": {
            "url": WCAG_JSON_URL,
            "sha256": hashlib.sha256(wcag_raw).hexdigest(),
        },
        "note": "Faithful text copy for lookup. The PDF is the authority; page numbers are printed pages.",
        "files": files,
        "tests": out_tests,
    }
    (HERE / "tt.json").write_text(
        json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"ok: {len(files)} files, {len(out_tests)} tests")


if __name__ == "__main__":
    main(sys.argv[1])
