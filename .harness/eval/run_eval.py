#!/usr/bin/env python3
"""End-to-end skill eval pipeline for testcase-generator.

The script is **offline only**: it never reaches out to the network and
never invokes an LLM.  Instead it does three things for every fixture
in ``test-fixtures/skill-eval/``:

1. **Prompt coverage** — every Phase 0..5 prompt must mention the
   fixture's input kind (markdown PRD, OpenAPI, source code, etc.).
2. **Capability coverage** — ``SKILL.md`` (and
   ``skill.manifest.json``) must declare the corresponding capability.
3. **Expected output paths** — for each fixture we look up the
   expected artifacts in ``.harness/eval/EXPECTED_OUTPUTS.md`` and
   verify those paths would be reachable under ``test-output/``.

A markdown report is written to stdout.  ``--format=json`` switches
the output to a JSON document suitable for CI gating.

Usage::

    python .harness/eval/run_eval.py                # markdown report
    python .harness/eval/run_eval.py --format=json  # JSON report
    python .harness/eval/run_eval.py --output=path  # also dump to file
    python .harness/eval/run_eval.py --strict       # warn -> fail

Exit codes
----------
* ``0`` — every check passed (or only warned, in non-strict mode).
* ``1`` — at least one check failed, or a warn in strict mode.
* ``2`` — eval could not run (missing file, bad config).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

EVAL_FILE = Path(__file__).resolve()
EVAL_DIR = EVAL_FILE.parent
HARNESS_DIR = EVAL_DIR.parent
REPO_ROOT = HARNESS_DIR.parent

FIXTURE_DIR = REPO_ROOT / "test-fixtures" / "skill-eval"
OUTPUT_DIR = REPO_ROOT / "test-output"
EXPECTED_OUTPUTS_DOC = EVAL_DIR / "EXPECTED_OUTPUTS.md"
SKILL_DOC = REPO_ROOT / "SKILL.md"
MANIFEST_DOC = REPO_ROOT / "skill.manifest.json"

PROMPT_FILES = (
    REPO_ROOT / "prompts" / "phase0_input_preprocessing_prompt.md",
    REPO_ROOT / "prompts" / "phase1_requirements_prompt.md",
    REPO_ROOT / "prompts" / "phase2_code_analysis_prompt.md",
    REPO_ROOT / "prompts" / "phase3_domain_analysis_prompt.md",
    REPO_ROOT / "prompts" / "phase4_mbt_design_prompt.md",
    REPO_ROOT / "prompts" / "phase5_testcase_generation_prompt.md",
)


# ---------------------------------------------------------------------------
# Fixture registry
#
# Each fixture is mapped to:
#   - the input kinds it represents (used to grep prompts for coverage),
#   - the SKILL.md capability token that should mention it,
#   - a list of expected artifact paths under test-output/ (relative).
#
# Keep this list in lockstep with .harness/eval/EXPECTED_OUTPUTS.md.
# ---------------------------------------------------------------------------


@dataclass
class FixtureSpec:
    name: str
    path: Path
    input_kinds: List[str]                # lowercase tokens to grep
    capability_tokens: List[str]          # tokens expected in SKILL.md
    expected_outputs: List[str] = field(default_factory=list)
    degraded: bool = False                # if True, output is allowed to be a "降级" draft
    notes: str = ""


def build_fixture_registry() -> List[FixtureSpec]:
    if not FIXTURE_DIR.exists():
        return []
    specs: List[FixtureSpec] = []
    for path in sorted(FIXTURE_DIR.iterdir()):
        if not path.is_file():
            continue
        stem = path.stem
        if stem == "login_prd":
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=["prd", "需求文档", "用户故事", "用例"],
                capability_tokens=["根据需求或 PRD 生成测试用例", "需求驱动模式"],
                expected_outputs=[
                    "phase1/01_requirements_summary.md",
                    "phase5/01_testcase_collection.md",
                ],
                notes="标准交付：覆盖正向、负向、边界值、安全锁定、追溯矩阵。",
            ))
        elif stem == "order_openapi":
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=["openapi", "接口", "契约", "request", "response"],
                capability_tokens=["根据 API 规范生成接口测试场景", "代码与接口契约辅助分析"],
                expected_outputs=[
                    "phase2/05_contract_test_derivation.md",
                    "phase5/01_testcase_collection.md",
                ],
                notes="API/契约测试：401/409/400/201 等状态码都要覆盖。",
            ))
        elif stem == "bugfix_regression":
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=["源代码", "缺陷", "bug", "regression", "补丁"],
                capability_tokens=["根据源代码或补丁上下文补充测试路径", "回归聚焦模式"],
                expected_outputs=[
                    "phase2/04_concurrency_analysis.md",
                    "phase5/01_testcase_collection.md",
                ],
                notes="回归聚焦：过期券在 min_spend 边界上必须拒绝。",
            ))
        elif stem == "ambiguous_requirement":
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=["自然语言", "模糊", "缺口", "ambiguous"],
                capability_tokens=["输入质量预处理", "歧义与风险识别"],
                expected_outputs=[
                    "phase0/00_input_validation_report.md",
                    "phase0/00_enhancement_suggestions.md",
                ],
                degraded=True,
                notes="降级路径：先输出风险摘要 + 缺失信息清单，再考虑测试草稿。",
            ))
        elif stem == "order_lifecycle":
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=["状态机", "lifecycle", "MBT", "审批", "状态流转"],
                capability_tokens=["MBT 导向测试设计", "领域模型与状态模型构建"],
                expected_outputs=[
                    "phase3/04_event_storming_model.md",
                    "phase4/04_mutation_testing_strategy.md",
                ],
                notes="MBT 路径：状态转换表 + 非法路径 + 覆盖准则 + 最小路径集。",
            ))
        else:
            specs.append(FixtureSpec(
                name=stem,
                path=path,
                input_kinds=[],
                capability_tokens=[],
                notes="未在 eval 注册表中登记的 fixture，跳过深度校验。",
            ))
    return specs


# ---------------------------------------------------------------------------
# Coverage checks
# ---------------------------------------------------------------------------


@dataclass
class CheckOutcome:
    name: str
    status: str  # pass | warn | fail | skip
    detail: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _check_prompt_coverage(spec: FixtureSpec) -> CheckOutcome:
    """Each Phase 0..5 prompt should mention at least one of the
    fixture's input kinds.  Phase 0 is exempted only for fixtures that
    do not carry any structured content (e.g. natural-language drafts
    in earlier states of the conversation)."""

    if not spec.input_kinds:
        return CheckOutcome("prompt_coverage", "skip", "no input_kind tokens defined")

    missing: List[str] = []
    for prompt_path in PROMPT_FILES:
        if not prompt_path.exists():
            missing.append(f"{prompt_path.name} (file missing)")
            continue
        text = _read_text(prompt_path)
        # A prompt "covers" the fixture if any of its input_kinds appears
        # case-insensitively.  Tokens are intentionally broad to match
        # the prompt's natural language.
        tokens_present = [t for t in spec.input_kinds if t.lower() in text.lower()]
        if not tokens_present:
            missing.append(f"{prompt_path.name} (no token match)")

    if missing:
        return CheckOutcome(
            "prompt_coverage",
            "warn",
            "no token match in: " + ", ".join(missing),
        )
    return CheckOutcome("prompt_coverage", "pass", "all 6 phase prompts mention this fixture kind")


def _check_capability(spec: FixtureSpec) -> CheckOutcome:
    if not spec.capability_tokens:
        return CheckOutcome("capability_coverage", "skip", "no capability tokens required")

    skill_text = _read_text(SKILL_DOC) if SKILL_DOC.exists() else ""
    manifest_text = _read_text(MANIFEST_DOC) if MANIFEST_DOC.exists() else ""
    readme_text = _read_text(REPO_ROOT / "README.md") if (REPO_ROOT / "README.md").exists() else ""
    # README is also a capability surface per AGENTS.md §4.5.
    haystack = skill_text + "\n" + manifest_text + "\n" + readme_text

    missing = [t for t in spec.capability_tokens if t not in haystack]
    if missing:
        return CheckOutcome(
            "capability_coverage",
            "fail",
            "SKILL.md / manifest 缺少声明: " + ", ".join(missing),
        )
    return CheckOutcome("capability_coverage", "pass", "SKILL.md + manifest 都声明了相关能力")


def _check_expected_outputs(spec: FixtureSpec) -> CheckOutcome:
    if not spec.expected_outputs:
        return CheckOutcome("expected_outputs", "skip", "no expected output paths declared")

    if not OUTPUT_DIR.exists():
        return CheckOutcome(
            "expected_outputs",
            "warn",
            f"test-output/ 不存在；expected paths 仅供参考：{', '.join(spec.expected_outputs)}",
        )

    found: List[str] = []
    missing: List[str] = []
    for rel in spec.expected_outputs:
        target = OUTPUT_DIR / rel
        if target.exists():
            found.append(rel)
        else:
            missing.append(rel)

    if missing and not found:
        return CheckOutcome(
            "expected_outputs",
            "fail",
            "缺少全部期望产物: " + ", ".join(missing),
        )
    if missing:
        return CheckOutcome(
            "expected_outputs",
            "warn",
            "部分期望产物未生成: " + ", ".join(missing) + " (已存在: " + ", ".join(found) + ")",
        )
    return CheckOutcome(
        "expected_outputs",
        "pass",
        f"全部 {len(found)} 个期望产物已存在于 test-output/: " + ", ".join(found),
    )


# ---------------------------------------------------------------------------
# Phase 0 quality threshold sanity
# ---------------------------------------------------------------------------


PHASE0_THRESHOLD = 80


def check_phase0_threshold_doc() -> CheckOutcome:
    """Cross-check that the Phase 0 ≥ 80 threshold is documented
    somewhere that the project agrees on (README, AGENTS.md, the
    Phase 0 prompt itself)."""

    candidates = [
        REPO_ROOT / "README.md",
        HARNESS_DIR / "AGENTS.md",
        REPO_ROOT / "prompts" / "phase0_input_preprocessing_prompt.md",
        REPO_ROOT / "resources" / "quality_checklist.md",
    ]
    needle = re.compile(r"(phase\s*0|P0|阶段\s*0)[^。\n]{0,30}80")
    for path in candidates:
        if not path.exists():
            continue
        text = _read_text(path)
        if needle.search(text):
            return CheckOutcome(
                "phase0_threshold_doc",
                "pass",
                f"{path.relative_to(REPO_ROOT)}: 文档化了 Phase 0 ≥ 80 阈值",
            )
    return CheckOutcome(
        "phase0_threshold_doc",
        "warn",
        f"未在 README/AGENTS.md/Phase 0 prompt 中找到 ≥{PHASE0_THRESHOLD} 阈值的明文声明",
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass
class FixtureReport:
    name: str
    path: str
    status: str
    notes: str
    checks: List[CheckOutcome]


def render_markdown(
    fixture_reports: Sequence[FixtureReport],
    global_checks: Sequence[CheckOutcome],
) -> str:
    lines = ["# testcase-generator skill eval report", ""]

    passed = sum(1 for fr in fixture_reports if fr.status == "pass")
    warned = sum(1 for fr in fixture_reports if fr.status == "warn")
    failed = sum(1 for fr in fixture_reports if fr.status == "fail")

    lines.extend([
        "## Summary",
        "",
        f"- Fixtures evaluated: {len(fixture_reports)}",
        f"- Passed: {passed}",
        f"- Warned: {warned}",
        f"- Failed: {failed}",
        "",
    ])

    lines.extend(["## Global checks", "", "| Check | Status | Detail |", "| --- | --- | --- |"])
    for item in global_checks:
        lines.append(f"| {item.name} | {item.status} | {item.detail} |")
    lines.append("")

    lines.append("## Fixtures")
    for fr in fixture_reports:
        lines.append(f"\n### `{fr.name}` — {fr.status}")
        if fr.notes:
            lines.append(f"> {fr.notes}")
        lines.append("")
        lines.append("| Check | Status | Detail |")
        lines.append("| --- | --- | --- |")
        for check in fr.checks:
            detail = check.detail.replace("|", r"\|")
            lines.append(f"| {check.name} | {check.status} | {detail} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def evaluate(spec: FixtureSpec) -> FixtureReport:
    checks = [
        _check_prompt_coverage(spec),
        _check_capability(spec),
        _check_expected_outputs(spec),
    ]
    if any(c.status == "fail" for c in checks):
        status = "fail"
    elif any(c.status == "warn" for c in checks):
        status = "warn"
    else:
        status = "pass"

    return FixtureReport(
        name=spec.name,
        path=str(spec.path.relative_to(REPO_ROOT)),
        status=status,
        notes=spec.notes,
        checks=checks,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Offline eval for testcase-generator skill fixtures.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, help="also write the report to this file")
    parser.add_argument("--strict", action="store_true", help="treat warn as fail")
    args = parser.parse_args(argv)

    if not FIXTURE_DIR.exists():
        print(f"eval: missing fixture directory: {FIXTURE_DIR}", file=sys.stderr)
        return 2

    specs = build_fixture_registry()
    if not specs:
        print("eval: no fixtures found", file=sys.stderr)
        return 2

    fixture_reports = [evaluate(spec) for spec in specs]
    global_checks = [check_phase0_threshold_doc()]

    if args.format == "json":
        payload = {
            "fixtures": [
                {
                    **{k: v for k, v in asdict(fr).items() if k != "checks"},
                    "checks": [asdict(c) for c in fr.checks],
                }
                for fr in fixture_reports
            ],
            "global_checks": [asdict(c) for c in global_checks],
        }
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        rendered = render_markdown(fixture_reports, global_checks)

    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    failed = [fr for fr in fixture_reports if fr.status == "fail"]
    warned = [fr for fr in fixture_reports if fr.status == "warn"]

    if failed:
        return 1
    if args.strict and warned:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
