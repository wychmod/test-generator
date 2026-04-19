#!/usr/bin/env python3
"""Audit whether the repository implements the capabilities declared in SKILL.md."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_skill_version(skill_text: str) -> str:
    for line in skill_text.splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def extract_manifest_version(manifest_path: Path) -> str:
    if not manifest_path.exists():
        return "unknown"
    try:
        manifest = json.loads(read_text(manifest_path))
    except json.JSONDecodeError:
        return "unknown"
    return str(manifest.get("版本", "unknown"))


def validate_schema(schema_path: Path) -> CheckResult:
    try:
        schema = json.loads(read_text(schema_path))
    except json.JSONDecodeError as exc:
        return CheckResult("schema_json", "fail", f"{schema_path} is invalid JSON: {exc}")

    required_top_level = {"project"}
    missing = sorted(required_top_level - set(schema.get("required", [])))
    if missing:
        return CheckResult("schema_json", "warn", f"Schema missing required top-level keys: {', '.join(missing)}")

    return CheckResult("schema_json", "pass", f"{schema_path} parsed successfully")


def validate_example_config(config_path: Path, schema_path: Path) -> CheckResult:
    try:
        config = json.loads(read_text(config_path))
        schema = json.loads(read_text(schema_path))
    except json.JSONDecodeError as exc:
        return CheckResult("example_config", "fail", f"JSON parse failed: {exc}")

    schema_name = config.get("$schema")
    schema_id = schema.get("$id")
    if schema_name != schema_id:
        return CheckResult(
            "example_config",
            "warn",
            f"Config $schema is '{schema_name}', expected '{schema_id}'",
        )

    missing = sorted(set(schema.get("required", [])) - set(config.keys()))
    if missing:
        return CheckResult("example_config", "fail", f"Example config missing required keys: {', '.join(missing)}")

    return CheckResult("example_config", "pass", f"{config_path} matches schema id and required keys")


def check_required_paths() -> List[CheckResult]:
    required_paths = {
        "phase0_prompt": ROOT / "prompts/phase0_input_preprocessing_prompt.md",
        "phase1_prompt": ROOT / "prompts/phase1_requirements_prompt.md",
        "phase2_prompt": ROOT / "prompts/phase2_code_analysis_prompt.md",
        "phase3_prompt": ROOT / "prompts/phase3_domain_analysis_prompt.md",
        "phase4_prompt": ROOT / "prompts/phase4_mbt_design_prompt.md",
        "phase5_prompt": ROOT / "prompts/phase5_testcase_generation_prompt.md",
        "requirements_template": ROOT / "templates/requirements_template.md",
        "state_diagram_template": ROOT / "templates/state_diagram_template.md",
        "testcase_template": ROOT / "templates/testcase_template.md",
        "quality_checklist": ROOT / "resources/quality_checklist.md",
        "testcase_formats": ROOT / "resources/testcase_formats.md",
        "feedback_template": ROOT / "resources/feedback_template.md",
        "output_artifacts": ROOT / "resources/output_artifacts.md",
        "distribution_doc": ROOT / "DISTRIBUTION.md",
        "manifest": ROOT / "skill.manifest.json",
        "prd_reader": ROOT / "scripts/prd_reader.py",
    }

    results = []
    for name, path in required_paths.items():
        status = "pass" if path.exists() else "fail"
        detail = f"{path} exists" if path.exists() else f"{path} is missing"
        results.append(CheckResult(name, status, detail))
    return results


def check_version_alignment(skill_path: Path, readme_path: Path, manifest_path: Path) -> CheckResult:
    skill_text = read_text(skill_path)
    readme_text = read_text(readme_path)
    skill_version = extract_skill_version(skill_text)
    manifest_version = extract_manifest_version(manifest_path)
    expected_version = manifest_version if skill_version == "unknown" else skill_version
    expected = f"v{expected_version}"
    if expected_version == "unknown":
        return CheckResult("version_alignment", "warn", "No version found in SKILL.md or skill.manifest.json")
    if expected in readme_text or expected_version in readme_text:
        return CheckResult("version_alignment", "pass", f"README references {expected_version}")
    return CheckResult("version_alignment", "warn", f"README does not reference {expected_version}")


def check_v21_capabilities(skill_path: Path) -> CheckResult:
    skill_text = read_text(skill_path)
    output_artifacts = ROOT / "resources/output_artifacts.md"
    combined_text = skill_text
    if output_artifacts.exists():
        combined_text += "\n" + read_text(output_artifacts)
    required_tokens = [
        "阶段 0",
        "反馈闭环",
        "配置 Schema",
        "混沌工程场景",
        "测试数据工厂",
        "变异测试策略",
    ]
    missing = [token for token in required_tokens if token not in combined_text]
    if missing:
        return CheckResult("skill_capability_matrix", "fail", f"Skill resources missing: {', '.join(missing)}")
    return CheckResult("skill_capability_matrix", "pass", "Chinese SKILL.md and resource files include the declared v2.1 capability markers")


def build_results() -> List[CheckResult]:
    skill_path = ROOT / "SKILL.md"
    readme_path = ROOT / "README.md"
    schema_path = ROOT / "config/testcase-config-schema.json"
    config_path = ROOT / "config/example-config.json"
    manifest_path = ROOT / "skill.manifest.json"

    results = [
        check_version_alignment(skill_path, readme_path, manifest_path),
        check_v21_capabilities(skill_path),
        validate_schema(schema_path),
        validate_example_config(config_path, schema_path),
    ]
    results.extend(check_required_paths())
    return results


def render_markdown(results: List[CheckResult]) -> str:
    lines = [
        "# Capability Audit Report",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for result in results:
        lines.append(f"| {result.name} | {result.status} | {result.detail} |")

    passed = sum(1 for result in results if result.status == "pass")
    warned = sum(1 for result in results if result.status == "warn")
    failed = sum(1 for result in results if result.status == "fail")

    lines.extend(
        [
            "",
            f"- Passed: {passed}",
            f"- Warned: {warned}",
            f"- Failed: {failed}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit testcase-generator capability coverage.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    results = build_results()
    failed = any(result.status == "fail" for result in results)

    if args.format == "json":
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(results))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
