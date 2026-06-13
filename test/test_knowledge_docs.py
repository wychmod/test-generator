import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
KB_SCRIPTS = ROOT / "knowledge" / "scripts"
sys.path.insert(0, str(KB_SCRIPTS))

import search  # noqa: E402


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


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

    def test_skill_docs_explain_kb_traceability(self):
        text = read_text("SKILL.md")

        self.assertIn("[参考知识]", text)
        self.assertIn("KB:", text)
        self.assertIn("知识库不能覆盖用户当前需求", text)

    def test_reference_knowledge_base_trigger_is_supported(self):
        triggers = search.detect_trigger("参考知识库生成登录用例")["triggers"]

        self.assertIn("*", triggers)
        self.assertIn("参考知识库", triggers["*"])


if __name__ == "__main__":
    unittest.main()
