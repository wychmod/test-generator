import tempfile
import unittest
from pathlib import Path

from devtools import skill_quality_audit


class SkillQualityAuditTests(unittest.TestCase):
    def write_minimal_runtime_docs(self, root: Path) -> None:
        runtime_text = (
            "testcase-generator 2.1.0\n"
            "Phase 0 Phase 1 Phase 5\n"
            "ISO/IEC/IEEE 29119-3:2021\n"
            "用例ID 用例标题 前置条件 测试数据 执行步骤 预期结果 "
            "优先级 测试类型 追溯 假设\n"
            "步骤可执行 预期结果 边界 负向 权限 状态流转 推断\n"
        )
        for relative_path in skill_quality_audit.RUNTIME_DOCS:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(runtime_text, encoding="utf-8")

    def test_static_audit_exposes_required_checks(self):
        results = skill_quality_audit.build_static_results(Path.cwd())
        names = {result.name for result in results}

        self.assertIn("version_consistency", names)
        self.assertIn("runtime_version_drift", names)
        self.assertIn("six_phase_pipeline", names)
        self.assertIn("standard_reference", names)
        self.assertIn("required_testcase_fields", names)
        self.assertIn("quality_gate_rules", names)

    def test_static_audit_scans_prompt_runtime_assets_for_version_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_minimal_runtime_docs(root)
            prompt = root / "prompts" / "phase1_requirements_prompt.md"
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(
                "generated_by: testcase-generator v2.0.0\n",
                encoding="utf-8",
            )

            results = skill_quality_audit.build_static_results(root)

        version_drift = next((item for item in results if item.name == "runtime_version_drift"), None)
        self.assertIsNotNone(version_drift)
        self.assertEqual(version_drift.status, "fail")
        self.assertIn("phase1_requirements_prompt.md", version_drift.detail)

    def test_output_audit_scores_formal_cases_against_quality_threshold(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "formal_case.md").write_text(
                "# 正式测试用例\n\n"
                "## 1. 基本信息卡\n\n"
                "| 用例ID | 用例标题 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 | 优先级 | 测试类型 | 追溯 | 假设 |\n"
                "|---|---|---|---|---|---|---|---|---|---|\n"
                "| TC-LOGIN-001 | 登录成功 | active 用户存在 | username/password | 输入账号密码并提交 | 状态码等于 200 且 token 非空 | P0 | Functional | REQ-LOGIN-001 | 无 |\n\n"
                "### 执行步骤\n\n"
                "| 步骤# | 操作描述 | 输入数据 | 预期结果 |\n"
                "|---|---|---|---|\n"
                "| 1 | 打开登录页 | /login | 页面返回 200 |\n\n"
                "### 预期结果\n\n"
                "| 预期结果描述 | 判定标准 | 验证方法 |\n"
                "|---|---|---|\n"
                "| 登录成功 | 响应状态码等于 200 | API Assert |\n",
                encoding="utf-8",
            )

            results = skill_quality_audit.build_output_results(output_dir)

        formal_result = next((item for item in results if item.name == "output_formal_testcase"), None)
        self.assertIsNotNone(formal_result)
        self.assertEqual(formal_result.status, "pass")
        self.assertIn("score=100", formal_result.detail)

    def test_output_audit_rejects_formal_case_without_required_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "bad_case.md").write_text(
                "# 正式测试用例\n\n"
                "| 用例ID | 标题 |\n"
                "|---|---|\n"
                "| TC-LOGIN-001 | 登录成功 |\n",
                encoding="utf-8",
            )

            results = skill_quality_audit.build_output_results(output_dir)

        self.assertTrue(any(result.status == "fail" for result in results))
        self.assertTrue(any("bad_case.md" in result.detail for result in results))

    def test_output_audit_accepts_ambiguous_degraded_draft(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "ambiguous_requirement.md").write_text(
                "# 风险摘要\n\n"
                "- 输入只说明“登录要好用”，验收标准不可判定。\n\n"
                "# 缺失信息清单\n\n"
                "- 未说明账号、密码、锁定策略和错误提示。\n\n"
                "# 降级版测试草稿\n\n"
                "| 模块 | 场景标题 | 假设项 |\n"
                "|---|---|---|\n"
                "| 登录 | 验证基础登录入口存在 | 假设存在用户名密码登录 |\n",
                encoding="utf-8",
            )

            results = skill_quality_audit.build_output_results(output_dir)

        self.assertTrue(results)
        self.assertTrue(all(result.status != "fail" for result in results))


if __name__ == "__main__":
    unittest.main()
