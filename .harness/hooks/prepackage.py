#!/usr/bin/env python3
"""Cross-platform pre-package check for the testcase-generator repository.

The script runs *every* audit in the project's governance chain so a
release only ships when all of them are green.  The order is the same as
the AGENTS.md "必跑命令" list.

Usage::

    python .harness/hooks/prepackage.py            # fail on issues
    python .harness/hooks/prepackage.py --dry-run  # report only, exit 0
    python .harness/hooks/prepackage.py --json     # structured output

Exit codes
----------
* ``0`` — every audit passed.
* ``1`` — at least one audit failed.
* ``2`` — a required tool (git, node, python module) is missing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence


HOOK_FILE = Path(__file__).resolve()
HARNESS_DIR = HOOK_FILE.parents[1]                  # .harness
REPO_ROOT = HARNESS_DIR.parent                      # test-generator/

CAPABILITY_AUDIT = REPO_ROOT / "devtools" / "capability_audit.py"
SKILL_QUALITY_AUDIT = REPO_ROOT / "devtools" / "skill_quality_audit.py"
DOC_CONSISTENCY_AUDIT = HARNESS_DIR / "scripts" / "doc_consistency_audit.py"
TEST_RUNNER = REPO_ROOT / "test"


@dataclass
class AuditOutcome:
    name: str
    status: str
    detail: str
    command: List[str] = field(default_factory=list)


def _run(cmd: Sequence[str], *, timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(cmd),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _summarise(name: str, cmd: Sequence[str], proc: subprocess.CompletedProcess) -> AuditOutcome:
    if proc.returncode == 0:
        return AuditOutcome(name, "pass", "ok", command=list(cmd))
    stderr_tail = (proc.stderr or "").strip().splitlines()[-3:]
    detail = " | ".join(line.strip() for line in stderr_tail if line.strip())
    if not detail:
        detail = f"exit={proc.returncode} (no stderr output)"
    return AuditOutcome(name, "fail", detail, command=list(cmd))


def audit_capability() -> AuditOutcome:
    if not CAPABILITY_AUDIT.exists():
        return AuditOutcome("capability_audit", "error", f"missing: {CAPABILITY_AUDIT}")
    cmd = [sys.executable, str(CAPABILITY_AUDIT)]
    return _summarise("capability_audit", cmd, _run(cmd))


def audit_skill_quality() -> AuditOutcome:
    if not SKILL_QUALITY_AUDIT.exists():
        return AuditOutcome("skill_quality_audit", "error", f"missing: {SKILL_QUALITY_AUDIT}")
    cmd = [sys.executable, str(SKILL_QUALITY_AUDIT)]
    return _summarise("skill_quality_audit", cmd, _run(cmd))


def audit_doc_consistency() -> AuditOutcome:
    if not DOC_CONSISTENCY_AUDIT.exists():
        return AuditOutcome(
            "doc_consistency_audit",
            "warn",
            f"doc_consistency_audit.py not found at {DOC_CONSISTENCY_AUDIT}; "
            "this is expected before the foundation task lands",
        )
    cmd = [sys.executable, str(DOC_CONSISTENCY_AUDIT)]
    return _summarise("doc_consistency_audit", cmd, _run(cmd))


def audit_node_tests() -> AuditOutcome:
    if not TEST_RUNNER.exists():
        return AuditOutcome("node_tests", "warn", f"no test/ directory at {TEST_RUNNER}")
    node = shutil.which("node")
    if node is None:
        return AuditOutcome("node_tests", "error", "node executable not on PATH")
    cmd = [node, "--test", str(TEST_RUNNER)]
    return _summarise("node_tests", cmd, _run(cmd, timeout=300))


# The order here matches the AGENTS.md "必跑命令" section: capability →
# skill quality → doc consistency → node tests.  We keep it explicit so
# the gate runner can be re-ordered in one place if the charter changes.
DEFAULT_AUDITS = (
    audit_capability,
    audit_skill_quality,
    audit_doc_consistency,
    audit_node_tests,
)


def render_markdown(outcomes: Sequence[AuditOutcome]) -> str:
    lines = [
        "# prepackage check report",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in outcomes:
        detail = item.detail.replace("|", r"\|") or "(no detail)"
        lines.append(f"| {item.name} | {item.status} | {detail} |")
    lines.extend([
        "",
        f"- Audits executed: {len(outcomes)}",
        f"- Audits passed:   {sum(1 for o in outcomes if o.status == 'pass')}",
        f"- Audits failed:   {sum(1 for o in outcomes if o.status in {'fail', 'error'})}",
        f"- Audits warned:   {sum(1 for o in outcomes if o.status == 'warn')}",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run every governance audit before packaging the skill."
    )
    parser.add_argument("--dry-run", action="store_true", help="report only, exit 0")
    parser.add_argument("--json", action="store_true", help="emit a JSON report on stdout")
    args = parser.parse_args(argv)

    outcomes: List[AuditOutcome] = [audit() for audit in DEFAULT_AUDITS]

    if args.json:
        print(json.dumps([asdict(o) for o in outcomes], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(outcomes))

    if args.dry_run:
        return 0

    if any(o.status in {"fail", "error"} for o in outcomes):
        failed = ", ".join(o.name for o in outcomes if o.status in {"fail", "error"})
        print(f"\nprepackage: failed checks: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
