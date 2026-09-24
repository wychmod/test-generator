import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
# 技能运行时内容位于 skills/testcase-generator/（Agent Skills 标准布局）
SKILL_DIR = "skills/testcase-generator"
SKILL_ROOT = ROOT / SKILL_DIR
KB_SCRIPTS = SKILL_ROOT / "knowledge" / "scripts"
sys.path.insert(0, str(KB_SCRIPTS))

import search  # noqa: E402


def read_text(relative_path: str) -> str:
    """读取技能树内的文件；参数相对技能树根（skills/testcase-generator/）。"""
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


class KnowledgeDocsTests(unittest.TestCase):
    def test_user_readme_prioritizes_copy_paste_llm_ingest_flow(self):
        text = read_text("knowledge/README.md")

        required_fragments = [
            "最短路径",
            "复制 `knowledge/llm-ingest-template.md`",
            "让大模型输出可索引 Markdown",
            "生成用例时说",
            "追溯引用",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, text)

    def test_llm_ingest_template_is_copy_pasteable(self):
        text = read_text("knowledge/llm-ingest-template.md")

        required_fragments = [
            "# 大模型知识库录入模板",
            "请把以下资料录入知识库",
            "必须输出且只输出 Markdown",
            "knowledge/sources/<slug>.md",
            "## 来源与处理说明",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, text)

    def test_phase_prompts_define_reference_knowledge_consumption(self):
        prompt_paths = [
            "prompts/phase0_input_preprocessing_prompt.md",
            "prompts/phase1_requirements_prompt.md",
            "prompts/phase5_testcase_generation_prompt.md",
        ]

        for prompt_path in prompt_paths:
            with self.subTest(prompt=prompt_path):
                text = read_text(prompt_path)
                self.assertIn("[参考知识]", text)
                self.assertIn("KB:", text)

    def skill_documentation_surface(self) -> str:
        """SKILL.md 只做能力声明与路由，细则在 references/。

        两者共同构成 Skill 的文档面 —— 断言应覆盖整体，而不是只盯入口文件，
        否则一旦按渐进披露原则下沉内容，测试就会误报失败。
        """
        paths = ["SKILL.md"] + sorted(
            path.relative_to(SKILL_ROOT).as_posix() for path in (SKILL_ROOT / "references").glob("*.md")
        )
        return "\n".join(read_text(path) for path in paths)

    def test_skill_docs_explain_kb_traceability(self):
        combined = self.skill_documentation_surface()

        self.assertIn("[参考知识]", combined)
        self.assertIn("KB:", combined)
        self.assertIn("知识库不能覆盖用户当前需求", combined)

    def test_skill_entry_routes_to_knowledge_base_reference(self):
        """入口必须显式路由到知识库参考文件，否则下沉后的细则不可达。"""
        self.assertIn("references/knowledge-base-usage.md", read_text("SKILL.md"))

    def test_reference_knowledge_base_trigger_is_supported(self):
        triggers = search.detect_trigger("参考知识库生成登录用例")["triggers"]

        self.assertIn("*", triggers)
        self.assertIn("参考知识库", triggers["*"])


if __name__ == "__main__":
    unittest.main()
