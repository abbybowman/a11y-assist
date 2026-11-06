"""Load the rules specs in docs/rules/ and their versions.

One spec per TT test, named `<id>-<short-name>.md` (e.g. `4c-no-keyboard-trap.md`
for 4.C). Each starts with front matter giving `tt_test`, `tt_name` and
`spec_version`. Files named `<id>-build-tasks.md` are build checklists and
files starting with `_` (e.g. `_template.md`) are authoring aids; neither is a
spec. Any other file in the folder must be a valid spec, so a spec with broken
front matter fails loudly instead of being skipped.

This module only reads metadata. It decides no outcome.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from tobi508.models import TestId

REQUIRED_KEYS = ("tt_test", "tt_name", "spec_version")
_FILENAME = re.compile(r"^(?P<id>[0-9]+[a-z])-(?P<short>[a-z0-9-]+)\.md$")
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class RuleSpecError(ValueError):
    """A file in the rules folder breaks the spec conventions."""


@dataclass(frozen=True)
class RuleSpec:
    test_id: TestId
    spec_version: str
    path: Path
    sha256: str

    def version_label(self) -> str:
        return f"{self.spec_version} (sha256:{self.sha256[:12]})"


def parse_front_matter(text: str) -> dict[str, str]:
    """Parse a `---` delimited block of `key: value` lines."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise RuleSpecError("no front matter (file must start with '---')")
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep or not key.strip():
            raise RuleSpecError(f"bad front matter line: {line!r}")
        key = key.strip()
        if key in meta:
            raise RuleSpecError(f"duplicate front matter key: {key}")
        meta[key] = value.strip()
    raise RuleSpecError("front matter is not closed with '---'")


def _test_id_for_prefix(prefix: str) -> str:
    """'4c' -> '4.C'."""
    return f"{prefix[:-1]}.{prefix[-1].upper()}"


def load_spec(path: Path) -> RuleSpec:
    m = _FILENAME.match(path.name)
    if not m:
        raise RuleSpecError(f"{path.name}: name must be <id>-<short-name>.md")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    try:
        meta = parse_front_matter(text)
    except RuleSpecError as e:
        raise RuleSpecError(f"{path.name}: {e}") from None
    missing = [k for k in REQUIRED_KEYS if not meta.get(k)]
    if missing:
        raise RuleSpecError(f"{path.name}: missing front matter {missing}")
    try:
        test_id = TestId(meta["tt_test"])
    except ValueError:
        raise RuleSpecError(
            f"{path.name}: unknown tt_test {meta['tt_test']!r}"
        ) from None
    if _test_id_for_prefix(m["id"]) != test_id.value:
        raise RuleSpecError(
            f"{path.name}: file prefix does not match tt_test {test_id.value}"
        )
    if meta["tt_name"] != test_id.tt_name:
        raise RuleSpecError(
            f"{path.name}: tt_name {meta['tt_name']!r} != {test_id.tt_name!r}"
        )
    if not _SEMVER.match(meta["spec_version"]):
        raise RuleSpecError(
            f"{path.name}: spec_version {meta['spec_version']!r} is not X.Y.Z"
        )
    # Hash with LF line endings so a Windows checkout records the same value.
    digest = hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    return RuleSpec(
        test_id=test_id, spec_version=meta["spec_version"], path=path, sha256=digest
    )


def load_specs(rules_dir: Path) -> dict[TestId, RuleSpec]:
    specs: dict[TestId, RuleSpec] = {}
    if not rules_dir.is_dir():
        return specs
    for path in sorted(rules_dir.glob("*.md")):
        if path.name.endswith("-build-tasks.md") or path.name.startswith("_"):
            continue
        spec = load_spec(path)
        if spec.test_id in specs:
            raise RuleSpecError(
                f"two specs for {spec.test_id.value}: "
                f"{specs[spec.test_id].path.name}, {path.name}"
            )
        specs[spec.test_id] = spec
    return specs


def spec_versions(rules_dir: Path) -> dict[str, str]:
    """TT test ID -> 'spec_version (sha256:...)' for every spec present."""
    return {t.value: s.version_label() for t, s in load_specs(rules_dir).items()}
