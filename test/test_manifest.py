"""devtools/manifest.py 单测：manifest 唯一解析入口。

覆盖要点：
1. 字段访问器返回正确类型与内容；
2. 缓存行为可控（use_cache=False 强制重读）；
3. 非法/缺失 manifest 抛 ManifestError 而非静默返回空；
4. `expand_runtime_entries` 的通配展开与 lib/activation.js 语义一致；
5. **分发通道语义**：`distribution_excludes` 不得被当作「永不发布」使用
   —— 这是本模块存在的主要理由（曾因此误报 bin/lib 泄漏）。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "devtools"))

import manifest as manifest_module  # noqa: E402


class RealManifestTests(unittest.TestCase):
    """针对仓库真实 manifest 的断言。"""

    def setUp(self):
        manifest_module.clear_cache()

    def test_version_is_a_semver_like_string(self):
        version = manifest_module.version()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_runtime_files_is_non_empty_list_of_strings(self):
        entries = manifest_module.runtime_files()
        self.assertIsInstance(entries, list)
        self.assertTrue(entries)
        self.assertTrue(all(isinstance(e, str) for e in entries))

    def test_host_entries_match_activation_environments(self):
        """manifest 声明的宿主必须与 lib/activation.js 的 ENVIRONMENTS 完全一致。"""
        hosts = set(manifest_module.host_entries())
        self.assertTrue(hosts)

        activation = REPO_ROOT / "lib" / "activation.js"
        if not activation.exists():
            self.skipTest("lib/activation.js not present")
        source = activation.read_text(encoding="utf-8")
        # ENVIRONMENTS 对象的顶层键：缩进两格的 `name: {`
        import re

        block = re.search(r"const ENVIRONMENTS = \{(.*?)\n\};", source, re.S)
        self.assertIsNotNone(block, "ENVIRONMENTS block not found")
        env_names = set(re.findall(r"^\s{2}([a-z][a-z0-9]*):\s*\{", block.group(1), re.M))

        self.assertEqual(
            hosts,
            env_names,
            f"manifest 宿主 {sorted(hosts)} != activation 环境 {sorted(env_names)}",
        )

    def test_host_entry_files_all_exist(self):
        for host, relative in manifest_module.host_entries().items():
            with self.subTest(host=host):
                self.assertTrue(
                    (REPO_ROOT / relative).is_file(),
                    f"{host} -> {relative} does not exist",
                )

    def test_expanded_runtime_files_all_exist_and_include_entry(self):
        expanded = manifest_module.expand_runtime_entries()
        self.assertTrue(expanded)
        for rel in expanded:
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file())

        skill_entry = manifest_module.load_manifest()[manifest_module.FIELD_ENTRY]
        self.assertIn(skill_entry, expanded)

    def test_expanded_runtime_files_excludes_tracked_local_artifacts(self):
        """展开结果不得包含知识库索引等本地产物。"""
        expanded = manifest_module.expand_runtime_entries()
        self.assertNotIn("skills/testcase-generator/knowledge/index.json", expanded)
        self.assertFalse(any("__pycache__" in p for p in expanded))


class DistributionChannelSemanticsTests(unittest.TestCase):
    """分发排除的语义边界 —— 本模块的核心设计约束。"""

    def setUp(self):
        manifest_module.clear_cache()

    def test_excludes_contains_npm_only_assets(self):
        """bin/ 与 lib/ 在「分发排除」里，但它们是 npm-only 资产，**不是**永不发布。

        这条断言固化了「分发排除 ≠ 永不发布」这一区别。若将来有人把它
        当成全局黑名单使用，这个测试会作为提醒存在。
        """
        excludes = manifest_module.distribution_excludes()
        self.assertIn("bin/test-generator.js", excludes)
        self.assertIn("lib/activation.js", excludes)

        # 但它们必须真的存在于仓库（即"被排除"不等于"不存在"）
        self.assertTrue((REPO_ROOT / "bin" / "test-generator.js").is_file())
        self.assertTrue((REPO_ROOT / "lib" / "activation.js").is_file())

    def test_excludes_does_not_include_canonical_skill_tree(self):
        """技能树是 canonical 源，绝不能被排除（否则整个技能丢失）。"""
        excludes = manifest_module.distribution_excludes()
        for pattern in excludes:
            normalized = pattern.rstrip("/").removesuffix("/**")
            self.assertNotEqual(
                normalized,
                "skills",
                "skills/ 是 canonical 技能树，不能进入分发排除",
            )

    def test_docs_are_explicitly_excluded(self):
        """docs/ 必须**显式**排除，而不是靠"运行时白名单"的副作用。"""
        excludes = manifest_module.distribution_excludes()
        normalized = {p.rstrip("/").removesuffix("/**") for p in excludes}
        self.assertIn("docs", normalized)


class SyntheticManifestTests(unittest.TestCase):
    """针对合成 manifest 的边界与错误处理。"""

    def _write(self, tmp: Path, payload) -> Path:
        path = tmp / "skill.manifest.json"
        path.write_text(
            payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def test_missing_manifest_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with self.assertRaises(manifest_module.ManifestError):
                manifest_module.load_manifest(missing)

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self._write(Path(tmp), "{ not json")
            with self.assertRaises(manifest_module.ManifestError):
                manifest_module.load_manifest(bad)

    def test_non_object_root_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self._write(Path(tmp), "[1, 2, 3]")
            with self.assertRaises(manifest_module.ManifestError):
                manifest_module.load_manifest(bad)

    def test_wrong_field_type_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self._write(
                Path(tmp),
                {manifest_module.FIELD_RUNTIME_FILES: "should-be-a-list"},
            )
            loaded = manifest_module.load_manifest(bad)
            with self.assertRaises(manifest_module.ManifestError):
                manifest_module.runtime_files(loaded)

    def test_defaults_when_optional_fields_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(Path(tmp), {manifest_module.FIELD_VERSION: "9.9.9"})
            loaded = manifest_module.load_manifest(path)
            self.assertEqual(manifest_module.version(loaded), "9.9.9")
            self.assertEqual(manifest_module.runtime_files(loaded), [])
            self.assertEqual(manifest_module.distribution_excludes(loaded), [])
            self.assertEqual(manifest_module.host_entries(loaded), {})
            self.assertEqual(manifest_module.npm_environments(loaded), [])

    def test_expand_handles_glob_directory_and_plain_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dir").mkdir()
            (root / "dir" / "a.md").write_text("a", encoding="utf-8")
            (root / "dir" / "nested").mkdir()
            (root / "dir" / "nested" / "b.md").write_text("b", encoding="utf-8")
            (root / "single.txt").write_text("s", encoding="utf-8")

            expanded = manifest_module.expand_runtime_entries(
                ["dir/**", "single.txt", "missing.txt"],
                root=root,
            )
            # 注意：expand 会隐式追加 DISTRIBUTION.md / skill.manifest.json（与
            # lib/activation.js 对齐），此处它们不存在所以不会出现。
            self.assertEqual(expanded, ["dir/a.md", "dir/nested/b.md", "single.txt"])

    def test_cache_reuse_and_forced_reread(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(Path(tmp), {manifest_module.FIELD_VERSION: "1.0.0"})
            first = manifest_module.load_manifest(path)
            # 用同一路径 + use_cache=False 能读到新内容
            self._write(Path(tmp), {manifest_module.FIELD_VERSION: "2.0.0"})
            second = manifest_module.load_manifest(path, use_cache=False)
            self.assertEqual(manifest_module.version(first), "1.0.0")
            self.assertEqual(manifest_module.version(second), "2.0.0")


class FieldConstantTests(unittest.TestCase):
    """字段名常量必须与真实 manifest 的键一致。"""

    def setUp(self):
        manifest_module.clear_cache()
        self.manifest = manifest_module.load_manifest()

    def test_core_field_constants_present_in_manifest(self):
        for field in (
            manifest_module.FIELD_NAME,
            manifest_module.FIELD_VERSION,
            manifest_module.FIELD_ENTRY,
            manifest_module.FIELD_RUNTIME_FILES,
            manifest_module.FIELD_EXCLUDES,
            manifest_module.FIELD_HOST_ENTRIES,
            manifest_module.FIELD_CAPABILITIES,
            manifest_module.FIELD_NPM_ENTRY,
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.manifest)

    def test_capabilities_count_is_seven(self):
        """核心能力固定 7 项 —— 多处审计依赖这个数字。"""
        capabilities = self.manifest[manifest_module.FIELD_CAPABILITIES]
        cn = capabilities.get("zh-CN", capabilities) if isinstance(capabilities, dict) else capabilities
        self.assertEqual(len(cn), 7)


class CrossLanguageFieldParityTests(unittest.TestCase):
    """JS 侧的 MANIFEST_FIELDS 必须与 Python 侧的 FIELD_* 常量逐字相同。

    这是 Point 1「单一数据源」的跨语言延伸：两侧读的是同一个 JSON，若字段名
    常量各自漂移，就会出现「改了 manifest 键名、只更新了一半消费者」的静默失败。
    """

    PYTHON_TO_JS = {
        "FIELD_VERSION": "version",
        "FIELD_ENTRY": "entry",
        "FIELD_RUNTIME_FILES": "runtimeFiles",
        "FIELD_HOST_ENTRIES": "hostEntries",
        "FIELD_EXCLUDES": "excludes",
        "FIELD_NPM_ENTRY": "npmEntry",
    }

    def setUp(self):
        manifest_module.clear_cache()
        self.activation = REPO_ROOT / "lib" / "activation.js"
        if not self.activation.exists():
            self.skipTest("lib/activation.js not present")
        self.source = self.activation.read_text(encoding="utf-8")

    def _js_manifest_fields(self) -> dict:
        import re

        block = re.search(r"const MANIFEST_FIELDS = \{(.*?)\n\};", self.source, re.S)
        self.assertIsNotNone(block, "lib/activation.js 中缺少 MANIFEST_FIELDS 常量")
        return dict(re.findall(r'(\w+):\s*"([^"]+)"', block.group(1)))

    def test_js_manifest_fields_exist(self):
        self.assertTrue(self._js_manifest_fields(), "MANIFEST_FIELDS 不得为空")

    def test_js_and_python_field_names_agree(self):
        js_fields = self._js_manifest_fields()
        for py_name, js_key in self.PYTHON_TO_JS.items():
            with self.subTest(python=py_name, js=js_key):
                py_value = getattr(manifest_module, py_name)
                self.assertIn(js_key, js_fields, f"JS 侧缺少字段键 {js_key}")
                self.assertEqual(
                    js_fields[js_key],
                    py_value,
                    f"{js_key}: JS 与 Python 的 manifest 字段名不一致",
                )

    def test_js_does_not_hardcode_manifest_keys_outside_constants(self):
        """除 MANIFEST_FIELDS 定义处外，不得再出现裸的中文 manifest 键字面量。"""
        import re

        stripped = re.sub(r"const MANIFEST_FIELDS = \{.*?\n\};", "", self.source, flags=re.S)
        leaked = sorted(
            set(re.findall(r'manifest\[\s*"([^"]+)"\s*\]', stripped))
        )
        self.assertEqual(
            leaked,
            [],
            f"lib/activation.js 仍在直接索引 manifest 中文字面量：{leaked}",
        )


if __name__ == "__main__":
    unittest.main()
