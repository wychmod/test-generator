from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from devtools import gen_plugin_manifests


ROOT = Path(__file__).resolve().parent.parent


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def quiet_main(argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return gen_plugin_manifests.main(argv)


class CommittedManifestTests(unittest.TestCase):
    """仓库中已提交的插件清单必须与 skill.manifest.json 一致。"""

    def test_check_passes_on_the_current_repo(self):
        self.assertEqual(quiet_main([]), 0)

    def test_plugin_relies_on_standard_skill_discovery(self):
        """技能位于标准的 skills/<name>/，客户端自动发现，不需要 skills 覆盖字段。"""
        plugin = read_json(".claude-plugin/plugin.json")

        self.assertEqual(plugin["name"], "testcase-generator")
        self.assertNotIn(
            "skills",
            plugin,
            "不应声明 skills 覆盖字段 —— 默认扫描已覆盖 skills/，覆盖反而引入未经验证的字段语义假设",
        )
        self.assertTrue(
            (ROOT / "skills" / "testcase-generator" / "SKILL.md").is_file(),
            "技能入口必须位于 skills/testcase-generator/SKILL.md",
        )

    def test_plugin_version_tracks_the_skill_manifest(self):
        self.assertEqual(
            read_json(".claude-plugin/plugin.json")["version"],
            read_json("skill.manifest.json")["版本"],
        )

    def test_marketplace_entry_points_at_the_plugin_root(self):
        marketplace = read_json(".claude-plugin/marketplace.json")

        self.assertIn("owner", marketplace)
        self.assertEqual(len(marketplace["plugins"]), 1)
        self.assertEqual(marketplace["plugins"][0]["source"], "./")
        self.assertEqual(marketplace["plugins"][0]["name"], "testcase-generator")

    def test_manifests_live_only_inside_the_plugin_directory(self):
        """Claude Code 规定 .claude-plugin/ 内只允许放 manifest。"""
        entries = {path.name for path in (ROOT / ".claude-plugin").iterdir()}

        self.assertEqual(entries, {"plugin.json", "marketplace.json"})


class GeneratorUnitTests(unittest.TestCase):
    SKILL = {
        "名称": {"zh-CN": "demo", "en-US": "demo-skill"},
        "显示名称": {"zh-CN": "演示", "en-US": "Demo Skill"},
        "说明": {"zh-CN": "演示说明", "en-US": "Demo description."},
        "版本": "1.0.0",
    }
    PACKAGE = {
        "author": "tester <t@example.com>",
        "license": "MIT",
        "homepage": "https://example.com",
        "keywords": ["demo"],
    }

    def patched(self, root: Path):
        plugin_dir = root / ".claude-plugin"
        return mock.patch.multiple(
            gen_plugin_manifests,
            ROOT=root,
            MANIFEST_PATH=root / "skill.manifest.json",
            PACKAGE_PATH=root / "package.json",
            PLUGIN_DIR=plugin_dir,
            PLUGIN_PATH=plugin_dir / "plugin.json",
            MARKETPLACE_PATH=plugin_dir / "marketplace.json",
        )

    def make_tree(self, root: Path) -> None:
        root.joinpath("skill.manifest.json").write_text(
            json.dumps(self.SKILL, ensure_ascii=False), encoding="utf-8"
        )
        root.joinpath("package.json").write_text(
            json.dumps(self.PACKAGE, ensure_ascii=False), encoding="utf-8"
        )

    def test_owner_name_strips_the_email_part(self):
        self.assertEqual(gen_plugin_manifests.owner_name("wychmod <a@b.c>"), "wychmod")
        self.assertEqual(gen_plugin_manifests.owner_name("plain"), "plain")

    def test_english_fields_are_selected_from_the_bilingual_manifest(self):
        plugin = gen_plugin_manifests.build_plugin(self.SKILL, self.PACKAGE)

        self.assertEqual(plugin["name"], "demo-skill")
        self.assertEqual(plugin["displayName"], "Demo Skill")
        self.assertEqual(plugin["description"], "Demo description.")
        self.assertEqual(plugin["version"], "1.0.0")
        self.assertNotIn("skills", plugin)

    def test_missing_plugin_json_is_reported_as_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)

            with self.patched(root):
                self.assertEqual(quiet_main([]), 1)

    def test_write_then_check_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)

            with self.patched(root):
                self.assertEqual(quiet_main(["--write"]), 0)
                self.assertEqual(quiet_main([]), 0)

            plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(plugin["author"]["name"], "tester")
            self.assertEqual(plugin["license"], "MIT")

            marketplace = json.loads(
                (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(marketplace["name"], "tester-demo-skill")
            self.assertEqual(marketplace["owner"]["name"], "tester")

    def test_stale_plugin_json_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)
            plugin_dir = root / ".claude-plugin"
            plugin_dir.mkdir(parents=True, exist_ok=True)
            (plugin_dir / "plugin.json").write_text('{"name": "stale"}', encoding="utf-8")

            with self.patched(root):
                self.assertEqual(quiet_main([]), 1)


if __name__ == "__main__":
    unittest.main()
