#!/usr/bin/env python3
"""Cross-platform pre-commit check for the testcase-generator repository.

The script reads the list of files staged for the next git commit and
runs the smallest set of audits that the diff actually requires.  It
mirrors the "必跑命令" list documented in ``.harness/AGENTS.md`` so the
hook never disagrees with the project charter.

Usage::

    python .harness/hooks/precommit.py            # fail on issues
    python .harness/hooks/precommit.py --dry-run  # report only, exit 0
    python .harness/hooks/precommit.py --all      # run every check, ignore the diff

Exit codes
----------
* ``0`` — every triggered check passed (or only reported in dry-run).
* ``1`` — at least one check failed.
* ``2`` — the script could not run (missing git, missing audit script, ...).

The script is intentionally importable so the same code paths can be
unit-tested from a CI runner.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

HOOK_FILE = Path(__file__).resolve()
HARNESS_DIR = HOOK_FILE.parents[1]                  # .harness
REPO_ROOT = HARNESS_DIR.parent                      # test-generator/

CAPABILITY_AUDIT = REPO_ROOT / "devtools" / "capability_audit.py"
SKILL_QUALITY_AUDIT = REPO_ROOT / "devtools" / "skill_quality_audit.py"
DOC_CONSISTENCY_AUDIT = HARNESS_DIR / "scripts" / "doc_consistency_audit.py"
TEST_RUNNER = REPO_ROOT / "test"
TEST_GENERATOR_CLI = REPO_ROOT / "bin" / "test-generator.js"
SKILL_MANIFEST = REPO_ROOT / "skill.manifest.json"


# ---------------------------------------------------------------------------
# Trigger table
#
# Each rule has a set of glob-style prefixes that, if present in the staged
# diff, activate one or more checks.  Keep this in sync with the wording
# used in the task brief and the AGENTS.md "必跑命令" section.
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Outcome of a single audit invocation."""

    name: str
    status: str  # "pass" | "fail" | "warn" | "skip" | "error"
    detail: str = ""
    command: Sequence[str] = field(default_factory=list)


def _matches_any(path: str, prefixes: Sequence[str]) -> bool:
    """Return True if *path* sits under any of the given prefixes."""

    normalized = path.replace("\\", "/").lstrip("./")
    for prefix in prefixes:
        clean_prefix = prefix.replace("\\", "/").rstrip("/")
        if normalized == clean_prefix or normalized.startswith(clean_prefix + "/"):
            return True
    return False


def classify(staged: Sequence[str]) -> dict:
    """Bucket the staged paths into the trigger groups from the brief."""

    paths = [p.replace("\\", "/") for p in staged if p.strip()]
    return {
        "manifest": [
            p for p in paths
            if _matches_any(p, ["SKILL.md", "skill.manifest.json", "package.json"])
        ],
        "prompts": [
            p for p in paths
            if _matches_any(p, ["prompts", "templates", "resources"])
        ],
        "runtime": [
            p for p in paths
            if _matches_any(p, ["lib", "bin"])
        ],
        "distribution": [
            p for p in paths
            if _matches_any(p, ["DISTRIBUTION.md"]) or p == "skill.manifest.json"
        ],
        "adapters": [
            p for p in paths
            if _matches_any(p, ["adapters"])
        ],
        "harness": [
            p for p in paths
            if _matches_any(p, [".harness"])
        ],
    }


# ---------------------------------------------------------------------------
# Audit runners
# ---------------------------------------------------------------------------


def _run_subprocess(cmd: Sequence[str], *, timeout: int = 180) -> subprocess.CompletedProcess:
    """Run *cmd* and capture its output, swallowing the exception types we
    actually expect.  Keeping the call in one place makes it easy to add
    tracing later and to keep the surface area small for tests."""

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


def _summarize(name: str, cmd: Sequence[str], proc: subprocess.CompletedProcess) -> CheckResult:
    if proc.returncode == 0:
        return CheckResult(name, "pass", "ok", command=list(cmd))

    # We deliberately do not include stdout in the detail: audit scripts
    # are noisy on success, and we want a one-line summary that the user
    # can act on.  Failures show stderr (which the auditors always fill).
    stderr_tail = (proc.stderr or "").strip().splitlines()[-3:]
    detail = " | ".join(line.strip() for line in stderr_tail if line.strip())
    if not detail:
        detail = f"exit={proc.returncode} (no stderr output)"
    return CheckResult(name, "fail", detail, command=list(cmd))


def run_capability_audit() -> CheckResult:
    if not CAPABILITY_AUDIT.exists():
        return CheckResult(
            "capability_audit",
            "error",
            f"missing audit script: {CAPABILITY_AUDIT}",
        )
    cmd = [sys.executable, str(CAPABILITY_AUDIT)]
    proc = _run_subprocess(cmd)
    return _summarize("capability_audit", cmd, proc)


def run_skill_quality_audit() -> CheckResult:
    if not SKILL_QUALITY_AUDIT.exists():
        return CheckResult(
            "skill_quality_audit",
            "error",
            f"missing audit script: {SKILL_QUALITY_AUDIT}",
        )
    cmd = [sys.executable, str(SKILL_QUALITY_AUDIT)]
    proc = _run_subprocess(cmd)
    return _summarize("skill_quality_audit", cmd, proc)


def run_node_tests() -> CheckResult:
    if not TEST_RUNNER.exists():
        return CheckResult(
            "node_tests",
            "warn",
            f"no test directory at {TEST_RUNNER}; skipping",
        )
    node = shutil.which("node")
    if node is None:
        return CheckResult("node_tests", "error", "node executable not on PATH")
    cmd = [node, "--test", str(TEST_RUNNER)]
    proc = _run_subprocess(cmd, timeout=240)
    return _summarize("node_tests", cmd, proc)


def run_cross_host_activation() -> CheckResult:
    if not TEST_GENERATOR_CLI.exists():
        return CheckResult(
            "cross_host_activation",
            "error",
            f"missing CLI entry: {TEST_GENERATOR_CLI}",
        )
    node = shutil.which("node")
    if node is None:
        return CheckResult("cross_host_activation", "error", "node executable not on PATH")

    envs_proc = _run_subprocess([node, str(TEST_GENERATOR_CLI), "environments"])
    if envs_proc.returncode != 0:
        return CheckResult(
            "cross_host_activation",
            "fail",
            f"`environments` command failed: exit={envs_proc.returncode}",
            command=[node, str(TEST_GENERATOR_CLI), "environments"],
        )
    envs = [line.strip() for line in envs_proc.stdout.splitlines() if line.strip()]
    if not envs:
        return CheckResult(
            "cross_host_activation",
            "fail",
            "`environments` returned an empty list",
        )

    failures: List[str] = []
    for env in envs:
        proc = _run_subprocess(
            [node, str(TEST_GENERATOR_CLI), "activate", env, "--dry-run"]
        )
        if proc.returncode != 0:
            stderr_tail = (proc.stderr or "").strip().splitlines()[-1:] or ["(no stderr)"]
            failures.append(f"{env}: {stderr_tail[0].strip()}")

    if failures:
        return CheckResult(
            "cross_host_activation",
            "fail",
            "; ".join(failures),
            command=[node, str(TEST_GENERATOR_CLI), "activate", "<env>", "--dry-run"],
        )
    return CheckResult(
        "cross_host_activation",
        "pass",
        f"{len(envs)} environment(s) dry-run ok: {', '.join(envs)}",
    )


# ---------------------------------------------------------------------------
# Sync reminders
# ---------------------------------------------------------------------------


def warn_distribution_sync(staged: Sequence[str]) -> CheckResult:
    """If either DISTRIBUTION.md or skill.manifest.json changed, the
    other document needs a human review.  We only emit a warning here:
    the actual content check belongs to doc_consistency_audit.py."""

    touched = [p for p in staged if p.replace("\\", "/") in {"DISTRIBUTION.md", "skill.manifest.json"}]
    if not touched:
        return CheckResult("distribution_sync", "skip", "no exclude-rule files staged")

    expected_companions = {
        "DISTRIBUTION.md": "skill.manifest.json 分发排除 / 运行时文件",
        "skill.manifest.json": "DISTRIBUTION.md 必入包 / 建议排除 表",
    }
    reminders: List[str] = []
    for changed in touched:
        companion = expected_companions.get(changed)
        if companion:
            reminders.append(f"{changed} 改了，请人工同步 {companion}")

    return CheckResult(
        "distribution_sync",
        "warn",
        "; ".join(reminders) if reminders else "staged but no rule-level change detected",
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def staged_paths() -> List[str]:
    """Return the list of files staged for commit, using porcelain v1."""

    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not on PATH")
    proc = subprocess.run(
        [git, "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"`git diff --cached` failed (exit={proc.returncode}): {proc.stderr.strip()}"
        )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def build_checks(trigger_buckets: dict, *, run_all: bool) -> List[CheckResult]:
    """Map the trigger buckets to actual audit invocations."""

    checks: List[CheckResult] = []

    if run_all or trigger_buckets["manifest"]:
        checks.append(run_capability_audit())

    if run_all or trigger_buckets["prompts"]:
        checks.append(run_skill_quality_audit())

    if run_all or trigger_buckets["runtime"]:
        checks.append(run_node_tests())

    if run_all or trigger_buckets["adapters"]:
        checks.append(run_cross_host_activation())

    if run_all or trigger_buckets["distribution"]:
        # The path list is not available here; the caller passes it via
        # the *staged* argument to warn_distribution_sync below.
        pass  # placeholder, real call lives in main()

    return checks


def render_report(
    staged: Sequence[str],
    buckets: dict,
    checks: Sequence[CheckResult],
    reminders: Sequence[CheckResult],
) -> str:
    lines: List[str] = ["# precommit check report", ""]
    if not staged and not checks and not reminders:
        lines.append("- No staged files detected; nothing to check.")
        return "\n".join(lines)
    if not staged:
        lines.append("- (no staged files; running with --all)")

    lines.append("## Triggered groups")
    for name, files in buckets.items():
        lines.append(f"- **{name}** ({len(files)}): " + (", ".join(files) if files else "—"))

    lines.extend(["", "## Checks", ""])
    lines.append("| Check | Status | Detail |")
    lines.append("| --- | --- | --- |")
    for item in list(checks) + list(reminders):
        detail = item.detail.replace("|", r"\|") or "(no detail)"
        lines.append(f"| {item.name} | {item.status} | {detail} |")

    failed = [c for c in checks if c.status in {"fail", "error"}]
    lines.extend([
        "",
        f"- Checks executed: {len(checks)}",
        f"- Checks passed:   {sum(1 for c in checks if c.status == 'pass')}",
        f"- Checks failed:   {len(failed)}",
        f"- Reminders:       {sum(1 for r in reminders if r.status == 'warn')}",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run audits against the staged subset of a testcase-generator commit.",
    )
    parser.add_argument("--dry-run", action="store_true", help="report only, never fail")
    parser.add_argument(
        "--all",
        action="store_true",
        help="run every audit regardless of the staged diff",
    )
    parser.add_argument(
        "--staged-file",
        action="append",
        default=None,
        help=argparse.SUPPRESS,  # only used by the testsuite
    )
    args = parser.parse_args(argv)

    try:
        if args.staged_file is not None:
            staged = list(args.staged_file)
        else:
            staged = staged_paths()
    except RuntimeError as exc:
        print(f"precommit: {exc}", file=sys.stderr)
        return 2

    buckets = classify(staged)
    checks = build_checks(buckets, run_all=args.all)

    reminders: List[CheckResult] = []
    if args.all or buckets["distribution"]:
        reminders.append(warn_distribution_sync(staged))

    print(render_report(staged, buckets, checks, reminders))

    if args.dry_run:
        return 0

    failed = [c for c in checks if c.status in {"fail", "error"}]
    if failed:
        names = ", ".join(c.name for c in failed)
        print(
            f"\nprecommit: {len(failed)} check(s) failed: {names}",
            file=sys.stderr,
        )
        return 1

    warnings = [r for r in reminders if r.status == "warn"]
    if warnings:
        print(
            f"\nprecommit: {len(warnings)} reminder(s) above (not blocking).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
