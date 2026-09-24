#!/usr/bin/env python3
"""Synchronize the package identity version across the skill.

Single source of truth: ``skill.manifest.json`` -> ``版本``.

Why this exists
---------------
Hosts read different files, so the version string is necessarily duplicated:
``SKILL.md`` front matter, ``package.json``, the ``> **版本**`` banner on every
runtime document, ``template_version``, ``generated_by`` ... Duplication is
fine; duplication *without a synchronizer* drifts. This script is the
synchronizer:

  python devtools/sync_version.py            # check (default) -> exit 1 on drift
  python devtools/sync_version.py --write    # propagate manifest version
  python devtools/sync_version.py --json     # machine-readable

Deliberately NOT touched (they are history, not identity):

* ``.harness/changelogs/**``            — historical release records
* ``[vX.Y 新增]`` / ``vX.Y 增强内容``   — feature attribution markers
* external spec URLs (Postman / SARIF / OAS) that legitimately contain ``v2.1.0``
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "skill.manifest.json"
README_PATH = ROOT / "README.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# --- Version markers --------------------------------------------------------
#
# Every pattern exposes exactly one named group ``ver`` holding the version
# literal. The replacement rebuilds the match by swapping that literal, so no
# pattern needs to know anything about its own surrounding text.

RULES: dict[str, re.Pattern[str]] = {
    # SKILL.md front matter: `version: 2.2.0`
    "frontmatter_version": re.compile(r"^version:[ \t]+(?P<ver>\d+\.\d+\.\d+)[ \t]*$", re.M),
    # skill.manifest.json: `"版本": "2.2.0"`
    "manifest_version": re.compile(r'"版本"[ \t]*:[ \t]*"(?P<ver>\d+\.\d+\.\d+)"'),
    # package.json top-level: `  "version": "2.2.0"`
    "package_version": re.compile(r'^  "version"[ \t]*:[ \t]*"(?P<ver>\d+\.\d+\.\d+)"', re.M),
    # runtime doc banner: `> **版本**: 2.2.0` / `> **模板版本**: 2.2.0`
    "doc_header": re.compile(r">[ \t]*\*\*(?:版本|模板版本)\*\*[ \t]*:[ \t]*(?P<ver>\d+\.\d+\.\d+)"),
    # YAML front matter inside templates: `template_version: "2.2.0"`
    "template_version": re.compile(r'template_version:[ \t]*"(?P<ver>\d+\.\d+\.\d+)"'),
    # Any self-identification of the tool: `generated_by: "... v2.2.0"`,
    # `generator: "... v2.2.0"`, prose such as `由 testcase-generator v2.2.0 提供`.
    # One rule covers all of them because it only ever rewrites the literal
    # right after the tool name.
    "tool_version_ref": re.compile(r"testcase-generator v(?P<ver>\d+\.\d+(?:\.\d+)?)"),
    # document H1: `# 测试用例格式参考 v2.2.0 (生产级)`.
    # A UTF-8 BOM may precede the `#`, so it has to be allowed explicitly.
    "doc_title": re.compile(r"^[ \t\uFEFF]*#(?!#)[^\n]*? v(?P<ver>\d+\.\d+(?:\.\d+)?) \(生产级\)", re.M),
    # generator author label: `AI Generator v2.2`
    "generator_label": re.compile(r"AI Generator v(?P<ver>\d+\.\d+(?:\.\d+)?)"),
    # config schema description: `测试用例生成器 v2.2 配置文件`
    "config_description": re.compile(r"测试用例生成器 v(?P<ver>\d+\.\d+(?:\.\d+)?) 配置文件"),
}

# Which rules apply to which files. Keeping an explicit allow-list (instead of
# running every rule over every file) is what makes this script safe to run.
SCOPES: list[tuple[str, list[str]]] = [
    ("SKILL.md", ["frontmatter_version"]),
    ("skill.manifest.json", ["manifest_version"]),
    ("package.json", ["package_version"]),
    ("config/*.json", ["config_description"]),
    ("prompts/*.md", ["doc_header", "tool_version_ref", "generator_label"]),
    ("resources/*.md", ["doc_header", "tool_version_ref", "doc_title", "generator_label"]),
    ("templates/*.md", ["doc_header", "template_version", "tool_version_ref", "doc_title", "generator_label"]),
]

# README is special: the project constitution requires the first H1 to carry
# `vX.Y.Z`, and it must be *inserted* when missing rather than only updated.
README_H1_RE = re.compile(r"^#(?!#)[ \t]*(?P<title>[^\n]*)$", re.M)
README_VERSION_RE = re.compile(r"v(?P<ver>\d+\.\d+\.\d+)")


@dataclass
class Finding:
    path: str
    rule: str
    found: str
    expected: str

    @property
    def ok(self) -> bool:
        return self.found == self.expected


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def read_source_version() -> str:
    manifest = json.loads(read_text(MANIFEST_PATH))
    version = str(manifest.get("版本", "")).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit(f"[error] {MANIFEST_PATH.name} 的 版本 字段不是 X.Y.Z 形式: {version!r}")
    return version


def rewrite(text: str, rule: re.Pattern[str], new_version: str) -> tuple[str, list[str]]:
    """Replace the version literal inside every match; return (new_text, olds)."""
    found: list[str] = []

    def repl(match: re.Match[str]) -> str:
        old = match.group("ver")
        if old != new_version:
            found.append(old)
        return match.group(0).replace(old, new_version, 1)

    return rule.sub(repl, text), found


def rewrite_readme_h1(text: str, new_version: str) -> tuple[str, str | None]:
    """Ensure the first H1 mentions vX.Y.Z. Returns (new_text, old_version)."""
    match = README_H1_RE.search(text)
    if not match:
        return text, None

    title = match.group("title")
    existing = README_VERSION_RE.search(title)
    old = existing.group("ver") if existing else None

    if existing:
        new_title = title[: existing.start()] + f"v{new_version}" + title[existing.end() :]
    else:
        # Append the version to the first `·`-separated segment of the title.
        segments = title.split("·")
        segments[0] = segments[0].rstrip() + f" v{new_version} "
        new_title = "·".join(segments).replace("  ", " ").rstrip()

    return text[: match.start("title")] + new_title + text[match.end("title") :], old


def iter_scope_files(pattern: str) -> list[Path]:
    if "*" not in pattern:
        path = ROOT / pattern
        return [path] if path.is_file() else []
    return sorted(ROOT.glob(pattern))


def collect(findings_out: list[Finding], new_version: str) -> None:
    for pattern, rule_names in SCOPES:
        for path in iter_scope_files(pattern):
            rel = path.relative_to(ROOT).as_posix()
            text = read_text(path)
            for rule_name in rule_names:
                for match in RULES[rule_name].finditer(text):
                    findings_out.append(
                        Finding(rel, rule_name, match.group("ver"), new_version)
                    )

    for match in README_H1_RE.finditer(read_text(README_PATH)):
        title = match.group("title")
        existing = README_VERSION_RE.search(title)
        findings_out.append(
            Finding("README.md", "readme_h1", existing.group("ver") if existing else "", new_version)
        )
        break


def apply_writes(new_version: str) -> list[Finding]:
    """Rewrite every scope file; return the findings that were actually fixed."""
    fixed: list[Finding] = []

    for pattern, rule_names in SCOPES:
        for path in iter_scope_files(pattern):
            rel = path.relative_to(ROOT).as_posix()
            text = read_text(path)
            original = text
            for rule_name in rule_names:
                text, olds = rewrite(text, RULES[rule_name], new_version)
                fixed.extend(Finding(rel, rule_name, old, new_version) for old in olds)
            if text != original:
                path.write_text(text, encoding="utf-8")

    text = read_text(README_PATH)
    new_text, old = rewrite_readme_h1(text, new_version)
    if new_text != text:
        README_PATH.write_text(new_text, encoding="utf-8")
        fixed.append(Finding("README.md", "readme_h1", old or "", new_version))

    return fixed


def render(findings: list[Finding], version: str) -> str:
    lines = [f"# Version Sync Report (source of truth: skill.manifest.json = {version})", ""]
    if not findings:
        lines.append("All version markers are in sync.")
        return "\n".join(lines)

    lines += ["| File | Rule | Found | Expected |", "| --- | --- | --- | --- |"]
    for item in findings:
        lines.append(f"| {item.path} | {item.rule} | {item.found or '(missing)'} | {item.expected} |")
    lines += ["", f"- Drifted markers: {len(findings)}"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync the skill identity version from skill.manifest.json.")
    parser.add_argument("--write", action="store_true", help="apply the manifest version to every marker")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    version = read_source_version()

    if args.write:
        fixed = apply_writes(version)
        if args.json:
            print(json.dumps({"version": version, "fixed": [asdict(f) for f in fixed]}, ensure_ascii=False, indent=2))
        else:
            print(render(fixed, version))
        return 0

    findings: list[Finding] = []
    collect(findings, version)
    drifted = [item for item in findings if not item.ok]

    if args.json:
        print(json.dumps({"version": version, "drifted": [asdict(f) for f in drifted]}, ensure_ascii=False, indent=2))
    else:
        print(render(drifted, version))

    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
