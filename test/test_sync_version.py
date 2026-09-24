from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from devtools import sync_version


def quiet_main(argv):
    """Run the CLI while swallowing its report output."""
    with contextlib.redirect_stdout(io.StringIO()):
        return sync_version.main(argv)


class SyncVersionUnitTests(unittest.TestCase):
    def test_source_of_truth_is_the_manifest_version(self):
        self.assertRegex(sync_version.read_source_version(), r"^\d+\.\d+\.\d+$")

    def test_rewrite_swaps_the_version_inside_a_matched_rule(self):
        text = "> **版本**: 2.1.0 | 标准: ISTQB"

        new_text, olds = sync_version.rewrite(text, sync_version.RULES["doc_header"], "2.2.0")

        self.assertEqual(olds, ["2.1.0"])
        self.assertIn("> **版本**: 2.2.0", new_text)

    def test_rewrite_is_a_noop_when_the_version_already_matches(self):
        text = 'generated_by: "testcase-generator v2.2.0"'

        new_text, olds = sync_version.rewrite(text, sync_version.RULES["tool_version_ref"], "2.2.0")

        self.assertEqual(olds, [])
        self.assertEqual(new_text, text)

    def test_tool_version_ref_also_covers_prose_references(self):
        text = "*本指南由 testcase-generator v2.1 提供。*"

        new_text, olds = sync_version.rewrite(text, sync_version.RULES["tool_version_ref"], "2.2.0")

        self.assertEqual(olds, ["2.1"])
        self.assertIn("testcase-generator v2.2.0", new_text)

    def test_readme_h1_gains_a_version_when_missing(self):
        new_text, old = sync_version.rewrite_readme_h1("# 🧪 Tool · 中文说明\n", "9.9.9")

        self.assertIsNone(old)
        self.assertEqual(new_text, "# 🧪 Tool v9.9.9 · 中文说明\n")

    def test_readme_h1_updates_an_existing_version(self):
        new_text, old = sync_version.rewrite_readme_h1("# 🧪 Tool v2.1.0 · 中文说明\n", "2.2.0")

        self.assertEqual(old, "2.1.0")
        self.assertEqual(new_text, "# 🧪 Tool v2.2.0 · 中文说明\n")

    def test_historical_feature_markers_are_never_touched(self):
        """`[v2.1 新增]` 记录能力归属，不属于身份标记。"""
        text = "## 8. [v2.1 新增] 非功能需求提取\n\n> **v2.1 增强内容**:\n"

        for rule in sync_version.RULES.values():
            new_text, _ = sync_version.rewrite(text, rule, "2.2.0")
            self.assertEqual(new_text, text)


class SyncVersionCliTests(unittest.TestCase):
    def make_tree(self, root: Path, prompt_version: str = "2.1.0") -> None:
        skill_root = root / sync_version.SKILL_DIR
        (skill_root / "prompts").mkdir(parents=True, exist_ok=True)
        (skill_root / "prompts" / "phase0.md").write_text(
            f"> **版本**: {prompt_version} | 阶段目标: demo\n", encoding="utf-8"
        )
        (skill_root / "SKILL.md").write_text(
            f"---\nname: demo\nversion: {prompt_version}\n---\n", encoding="utf-8"
        )
        (root / "README.md").write_text(
            f"# Demo Tool v{prompt_version} · 说明\n", encoding="utf-8"
        )
        (root / "skill.manifest.json").write_text(
            json.dumps({"版本": "2.2.0"}, ensure_ascii=False), encoding="utf-8"
        )

    def patched(self, root: Path):
        return mock.patch.multiple(
            sync_version,
            ROOT=root,
            MANIFEST_PATH=root / "skill.manifest.json",
            README_PATH=root / "README.md",
        )

    def test_check_fails_on_drift_then_write_repairs_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)

            with self.patched(root):
                self.assertEqual(quiet_main([]), 1, "存在漂移时 --check 应失败")
                self.assertEqual(quiet_main(["--write"]), 0)
                self.assertEqual(quiet_main([]), 0, "回写后 --check 应通过")

            skill_root = root / sync_version.SKILL_DIR
            self.assertIn("2.2.0", (skill_root / "prompts" / "phase0.md").read_text(encoding="utf-8"))
            self.assertIn("2.2.0", (skill_root / "SKILL.md").read_text(encoding="utf-8"))
            self.assertIn("v2.2.0", (root / "README.md").read_text(encoding="utf-8"))

    def test_write_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root, prompt_version="2.2.0")

            with self.patched(root):
                self.assertEqual(quiet_main([]), 0, "已一致时 --check 应通过")
                before = (root / "README.md").read_text(encoding="utf-8")
                self.assertEqual(quiet_main(["--write"]), 0)
                after = (root / "README.md").read_text(encoding="utf-8")

            # 重复 --write 不应产生任何变化（README 也不会被重复插入版本号）
            self.assertEqual(before, after)
            self.assertEqual(after, "# Demo Tool v2.2.0 · 说明\n")

    def test_missing_manifest_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            (root / "skill.manifest.json").write_text(
                json.dumps({"版本": "not-a-version"}, ensure_ascii=False), encoding="utf-8"
            )

            with self.patched(root):
                with self.assertRaises(SystemExit):
                    sync_version.read_source_version()


if __name__ == "__main__":
    unittest.main()
