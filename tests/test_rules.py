"""Rules spec loading and the spec versions recorded in reports."""

from __future__ import annotations

from pathlib import Path

import pytest

from a11y_assist.config import REPO_ROOT, Settings
from a11y_assist.models import TestId
from a11y_assist.rules import RuleSpecError, load_specs, spec_versions
from a11y_assist.versions import collect_versions

RULES_DIR = REPO_ROOT / "docs" / "rules"

SPEC_4C = """---
tt_test: 4.C
tt_name: 2.1.2-no-keyboard-trap
spec_version: 1.2.3
---

# body
"""


def test_repo_specs_load_and_4c_version_comes_from_front_matter() -> None:
    specs = load_specs(RULES_DIR)
    # The versioning standard (docs/rules/_template.md): a spec is 0.y.z (a
    # draft, no outcome) exactly when no check is registered for it.
    from a11y_assist.checks import REGISTRY

    assert TestId.T4C in specs
    for t, spec in specs.items():
        assert spec.spec_version.startswith("0.") == (t not in REGISTRY), (
            t,
            spec.spec_version,
        )
    assert specs[TestId.T4C].spec_version == "1.6.0"
    assert specs[TestId.T4C].path.name == "4c-no-keyboard-trap.md"


def test_every_rules_file_is_a_spec_or_build_tasks() -> None:
    # load_specs raises on any non-build-tasks file that is not a valid spec.
    names = {p.name for p in RULES_DIR.glob("*.md")}
    spec_names = {s.path.name for s in load_specs(RULES_DIR).values()}
    assert names - spec_names <= {
        p for p in names if p.endswith("-build-tasks.md") or p.startswith("_")
    }


def test_version_recorded_in_report_versions(tmp_path: Path) -> None:
    (tmp_path / "4c-no-keyboard-trap.md").write_text(SPEC_4C)
    s = Settings(_env_file=None, rules_dir=tmp_path)
    v = collect_versions(s, None)
    assert v.rules_spec["4.C"].startswith("1.2.3 (sha256:")


def test_hash_ignores_line_endings(tmp_path: Path) -> None:
    (tmp_path / "4c-no-keyboard-trap.md").write_text(SPEC_4C)
    lf = spec_versions(tmp_path)
    (tmp_path / "4c-no-keyboard-trap.md").write_bytes(
        SPEC_4C.replace("\n", "\r\n").encode()
    )
    assert spec_versions(tmp_path) == lf


@pytest.mark.parametrize(
    ("name", "text", "msg"),
    [
        ("4c-no-keyboard-trap.md", "# no front matter\n", "no front matter"),
        (
            "4c-no-keyboard-trap.md",
            SPEC_4C.replace("spec_version: 1.2.3\n", ""),
            "missing",
        ),
        ("4c-no-keyboard-trap.md", SPEC_4C.replace("1.2.3", "v1"), "X.Y.Z"),
        ("4d-no-keyboard-trap.md", SPEC_4C, "prefix"),
        ("4c-no-keyboard-trap.md", SPEC_4C.replace("4.C", "4.Z"), "unknown"),
        ("4c-no-keyboard-trap.md", SPEC_4C.replace("2.1.2-no", "2.1.2-x"), "tt_name"),
        ("notes.md", SPEC_4C, "name must be"),
    ],
)
def test_bad_specs_fail_loudly(tmp_path: Path, name: str, text: str, msg: str) -> None:
    (tmp_path / name).write_text(text)
    with pytest.raises(RuleSpecError, match=msg):
        load_specs(tmp_path)


def test_two_specs_for_one_test_fail(tmp_path: Path) -> None:
    (tmp_path / "4c-no-keyboard-trap.md").write_text(SPEC_4C)
    (tmp_path / "4c-other.md").write_text(SPEC_4C)
    with pytest.raises(RuleSpecError, match="two specs"):
        load_specs(tmp_path)


def test_build_tasks_file_is_not_a_spec(tmp_path: Path) -> None:
    (tmp_path / "4c-build-tasks.md").write_text("# Build tasks\n")
    assert load_specs(tmp_path) == {}


def test_template_is_not_a_spec() -> None:
    # The repo template has placeholder front matter (tt_test: X.Y) that would
    # fail validation; the leading underscore keeps it out of the loader.
    assert (RULES_DIR / "_template.md").is_file()
    assert all(s.path.name != "_template.md" for s in load_specs(RULES_DIR).values())
