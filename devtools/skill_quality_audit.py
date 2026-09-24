#!/usr/bin/env python3
"""Audit testcase-generator skill quality against testcase authoring standards."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
# 技能运行时内容的唯一位置（Agent Skills 标准布局）。
# 注意：`skills/` 是 canonical 源，**不是**镜像目录。
SKILL_DIR = "skills/testcase-generator"

RUNTIME_DOCS = [
    f"{SKILL_DIR}/{relative}"
    for relative in (
        "SKILL.md",
        "prompts/phase0_input_preprocessing_prompt.md",
        "prompts/phase1_requirements_prompt.md",
        "prompts/phase2_code_analysis_prompt.md",
        "prompts/phase3_domain_analysis_prompt.md",
        "prompts/phase4_mbt_design_prompt.md",
        "prompts/phase5_testcase_generation_prompt.md",
        "references/delivery-protocol.md",
        "references/quality-review.md",
        "references/knowledge-base-usage.md",
        "resources/quality_checklist.md",
        "resources/testcase_formats.md",
        "templates/testcase_template.md",
        "templates/requirements_template.md",
        "templates/state_diagram_template.md",
    )
]
REQUIRED_TESTCASE_FIELDS = [
    "用例ID",
    "用例标题",
    "前置条件",
    "测试数据",
    "执行步骤",
    "预期结果",
    "优先级",
    "测试类型",
    "追溯",
    "假设",
]
QUALITY_RULE_TOKENS = [
    "步骤可执行",
    "预期结果",
    "边界",
    "负向",
    "权限",
    "状态流转",
    "推断",
]
# 任何与 skill.manifest.json 当前版本不一致的 `testcase-generator vX.Y[.Z]`
# 自引用都算版本漂移。用动态比对替代写死的旧版本字面量清单 —— 否则审计脚本
# 自己就会成为下一个漂移点（此前这里硬编码了 "2.1.0"，升级后必然误报）。
VERSION_REF_RE = re.compile(r"testcase-generator v(?P<ver>\d+\.\d+(?:\.\d+)?)")
FORMAL_SCORE_THRESHOLD = 90
EXECUTABLE_STEP_TOKENS = ["执行步骤", "操作描述", "输入数据"]
BINARY_EXPECTED_TOKENS = ["判定标准", "验证方法", "Pass/Fail", "等于", "应当", "状态码", "非空"]
COVERAGE_SIGNAL_TOKENS = [
    "Functional",
    "API",
    "UI",
    "E2E",
    "Security",
    "Performance",
    "Compatibility",
    "Regression",
    "Boundary",
    "Negative",
    "正向",
    "负向",
    "边界",
    "权限",
    "状态",
    "安全",
    "回归",
    "异常",
]
TRACEABILITY_TOKENS = ["追溯", "关联需求", "REQ-", "PATH-", "TT-"]
ASSUMPTION_TOKENS = ["假设", "缺口", "待确认", "推断", "歧义"]


@dataclass
class AuditResult:
    name: str
    status: str
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def combined_runtime_text(root: Path) -> str:
    chunks = []
    for relative_path in RUNTIME_DOCS:
        path = root / relative_path
        if path.exists():
            chunks.append(read_text(path))
    return "\n".join(chunks)


def manifest_version(root: Path) -> str:
    """当前版本以 skill.manifest.json 为单一数据源。"""
    path = root / "skill.manifest.json"
    if not path.exists():
        return ""
    try:
        return str(json.loads(read_text(path)).get("版本", "")).strip()
    except json.JSONDecodeError:
        return ""


def find_stale_runtime_markers(root: Path) -> list[str]:
    current = manifest_version(root)
    if not current:
        return ["skill.manifest.json: 版本 字段缺失或不可解析"]
    findings: list[str] = []
    for relative_path in RUNTIME_DOCS:
        path = root / relative_path
        if not path.exists():
            continue
        text = read_text(path)
        for match in VERSION_REF_RE.finditer(text):
            if match.group("ver") != current:
                findings.append(f"{relative_path}: {match.group(0)} -> expected v{current}")
    return findings


def result(name: str, ok: bool, detail: str, warn: bool = False) -> AuditResult:
    if ok:
        return AuditResult(name, "pass", detail)
    return AuditResult(name, "warn" if warn else "fail", detail)


def build_static_results(root: Path = ROOT) -> list[AuditResult]:
    text = combined_runtime_text(root)
    checklist = root / SKILL_DIR / "resources/quality_checklist.md"
    quality_text = read_text(checklist) if checklist.exists() else ""
    stale_markers = find_stale_runtime_markers(root)

    current = manifest_version(root)
    results = [
        result(
            "version_consistency",
            bool(current) and VERSION_REF_RE.search(text) is not None,
            f"Runtime docs carry testcase-generator v{current} provenance markers"
            if current
            else "skill.manifest.json 版本 字段缺失",
        ),
        result(
            "runtime_version_drift",
            not stale_markers,
            f"No version drift; every provenance marker matches v{current}"
            if not stale_markers
            else "; ".join(stale_markers),
        ),
        result(
            "six_phase_pipeline",
            all(token in text for token in ["Phase 0", "Phase 1", "Phase 5"]) and "五阶段" not in text,
            "Runtime docs describe the six-phase Phase 0-5 pipeline",
        ),
        result(
            "standard_reference",
            "ISO/IEC/IEEE 29119-3:2021" in text and "IEEE 829" not in text,
            "Runtime docs prefer ISO/IEC/IEEE 29119-3:2021 and avoid IEEE 829 as a current standard",
        ),
        result(
            "required_testcase_fields",
            all(token in text for token in REQUIRED_TESTCASE_FIELDS),
            "Runtime docs include all required testcase field names",
        ),
        result(
            "quality_gate_rules",
            all(token in quality_text for token in QUALITY_RULE_TOKENS),
            "Quality checklist covers executable steps, binary expected results, boundary/negative/permission/state-flow coverage, and inference marking",
        ),
    ]
    return results


def markdown_files(output_dir: Path) -> Iterable[Path]:
    if not output_dir.exists():
        return []
    return sorted(path for path in output_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".feature", ".yaml", ".yml", ".json"})


def is_formal_testcase(content: str) -> bool:
    return any(token in content for token in ["正式测试用例", 'document_type: "testcase"', "## 1. 基本信息卡", "TC-"])


def is_degraded_ambiguous_draft(content: str) -> bool:
    required = ["风险摘要", "缺失信息", "降级"]
    return all(token in content for token in required)


def is_gherkin(content: str, path: Path) -> bool:
    return path.suffix.lower() == ".feature" or "Feature:" in content


def is_api_format(content: str) -> bool:
    lowered = content.lower()
    return "request" in lowered and ("response" in lowered or "status code" in lowered)


def score_formal_testcase(content: str) -> tuple[int, list[str]]:
    score = 0
    missing: list[str] = []

    missing_fields = [token for token in REQUIRED_TESTCASE_FIELDS if token not in content]
    if not missing_fields:
        score += 20
    else:
        missing.append("字段完整性:" + ",".join(missing_fields))

    if all(token in content for token in EXECUTABLE_STEP_TOKENS):
        score += 20
    else:
        missing.append("步骤可执行")

    if "预期结果" in content and any(token in content for token in BINARY_EXPECTED_TOKENS):
        score += 20
    else:
        missing.append("二元可判定预期结果")

    if "测试类型" in content and any(token in content for token in COVERAGE_SIGNAL_TOKENS):
        score += 20
    else:
        missing.append("覆盖类型信号")

    has_traceability = any(token in content for token in TRACEABILITY_TOKENS)
    has_assumption_handling = any(token in content for token in ASSUMPTION_TOKENS)
    if has_traceability and has_assumption_handling:
        score += 20
    else:
        missing.append("追溯或假设/缺口标记")

    return score, missing


def evaluate_output_file(path: Path) -> AuditResult:
    content = read_text(path)
    missing: list[str] = []

    if is_degraded_ambiguous_draft(content):
        return AuditResult("output_degraded_draft", "pass", f"{path.name}: ambiguous input handled as degraded draft")

    if is_gherkin(content, path):
        missing = [token for token in ["Feature:", "Scenario", "Given", "When", "Then"] if token not in content]
        return result("output_gherkin_format", not missing, f"{path.name}: missing {', '.join(missing) if missing else 'none'}")

    if is_api_format(content):
        required = ["Request", "Expected Response", "Status", "Schema", "Error"]
        missing = [token for token in required if token not in content]
        return result("output_api_format", not missing, f"{path.name}: missing {', '.join(missing) if missing else 'none'}")

    if is_formal_testcase(content):
        score, missing = score_formal_testcase(content)
        detail = f"{path.name}: score={score}; missing {', '.join(missing) if missing else 'none'}"
        return result("output_formal_testcase", score >= FORMAL_SCORE_THRESHOLD, detail)

    compact_claims_formal = "正式测试用例" in content and "步骤摘要" in content
    return result(
        "output_lightweight_format",
        not compact_claims_formal,
        f"{path.name}: lightweight output does not claim formal testcase status",
    )


def build_output_results(output_dir: Path) -> list[AuditResult]:
    files = list(markdown_files(output_dir))
    if not files:
        return [AuditResult("output_files", "warn", f"No auditable output files found in {output_dir}")]
    results = [evaluate_output_file(path) for path in files]
    formal_results = [item for item in results if item.name == "output_formal_testcase"]
    if formal_results:
        passed = sum(1 for item in formal_results if item.status == "pass")
        pass_rate = int(round((passed / len(formal_results)) * 100))
        results.append(
            result(
                "output_formal_pass_rate",
                pass_rate >= FORMAL_SCORE_THRESHOLD,
                f"pass_rate={pass_rate}; threshold={FORMAL_SCORE_THRESHOLD}; formal_files={len(formal_results)}",
            )
        )
    return results


def render_markdown(results: list[AuditResult]) -> str:
    lines = [
        "# Skill Quality Audit Report",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in results:
        lines.append(f"| {item.name} | {item.status} | {item.detail} |")
    passed = sum(1 for item in results if item.status == "pass")
    warned = sum(1 for item in results if item.status == "warn")
    failed = sum(1 for item in results if item.status == "fail")
    lines.extend(["", f"- Passed: {passed}", f"- Warned: {warned}", f"- Failed: {failed}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit testcase-generator skill authoring quality.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--outputs", type=Path, help="Optional generated output directory to audit")
    args = parser.parse_args()

    results = build_static_results(ROOT)
    if args.outputs:
        results.extend(build_output_results(args.outputs))

    if args.format == "json":
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(results))

    return 1 if any(item.status == "fail" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
