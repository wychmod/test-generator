#!/usr/bin/env python3
"""Generate client plugin manifests from the canonical skill manifest.

`skill.manifest.json` stays the single source of truth. Client ecosystems
expect their own manifest files; instead of hand-maintaining them (and letting
them drift, the way the version markers did), we *compile* them.

Emits:

  .claude-plugin/plugin.json        Claude Code plugin manifest
  .claude-plugin/marketplace.json   single-plugin marketplace for the repo

Usage:
  python devtools/gen_plugin_manifests.py            # check -> exit 1 on drift
  python devtools/gen_plugin_manifests.py --write    # regenerate
  python devtools/gen_plugin_manifests.py --stdout   # preview only

Notes
-----
* The skill tree lives at ``skills/testcase-generator/`` (the Agent Skills
  standard layout), so clients discover it automatically. We deliberately do
  **not** emit a ``skills`` field: the default scan already covers ``skills/``,
  and omitting the override removes an assumption about field semantics that we
  could not verify against a real client here.
* ``.claude-plugin/`` may contain manifests ONLY — never component
  directories. Component paths live at the plugin root.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "skill.manifest.json"
PACKAGE_PATH = ROOT / "package.json"
PLUGIN_DIR = ROOT / ".claude-plugin"
PLUGIN_PATH = PLUGIN_DIR / "plugin.json"
MARKETPLACE_PATH = PLUGIN_DIR / "marketplace.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _MANIFEST():
    """惰性导入 devtools/manifest.py —— 字段名常量与 manifest 解析的唯一入口。"""
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    import manifest as manifest_module  # noqa: PLC0415

    return manifest_module


# 清单文本取自 manifest 双语字段的哪一侧。
# 公开插件市场是英文优先，因此默认 en-US；另一侧仍完整保留在 manifest 里，
# 将来若面向中文市场发布，只需改这一处。
MANIFEST_LANGUAGE = "en-US"


def first(value: dict | str, language: str = MANIFEST_LANGUAGE) -> str:
    """Pick a value out of the manifest's bilingual {zh-CN, en-US} maps."""
    if isinstance(value, str):
        return value
    return str(value.get(language) or next(iter(value.values()), ""))


def owner_name(author: str) -> str:
    """`"wychmod <a@b.c>"` -> `"wychmod"`."""
    return author.split("<", 1)[0].strip() or author.strip()


def build_plugin(skill: dict, pkg: dict) -> dict:
    m = _MANIFEST()
    name = first(skill[m.FIELD_NAME])
    return {
        "name": name,
        "displayName": first(skill[m.FIELD_DISPLAY_NAME]),
        "description": first(skill[m.FIELD_DESCRIPTION]),
        "version": str(skill[m.FIELD_VERSION]),
        "license": pkg.get("license", "MIT"),
        "author": {"name": owner_name(pkg.get("author", ""))},
        "homepage": pkg.get("homepage", ""),
        "repository": (pkg.get("repository") or {}).get("url", ""),
        "keywords": pkg.get("keywords", []),
    }


def build_marketplace(skill: dict, pkg: dict) -> dict:
    owner = owner_name(pkg.get("author", ""))
    name = first(skill[_MANIFEST().FIELD_NAME])
    # 市场级描述与插件描述是两回事：前者说明"这个市场提供什么"，后者说明
    # "这个技能做什么"。缺失时 `claude plugin validate` 会发出告警。
    #
    # 位置**只能**是 `metadata.description`。曾经同时写过顶层 `description`
    # （某些社区规范称其为正式位置），但校验器对未知顶层键是**报错**而非忽略：
    #     ✘ root: Unrecognized key: "description"
    # 因此这里严格只给一个位置 —— 多给字段不是冗余，是会直接弄坏构建。
    marketplace_description = first(skill[_MANIFEST().FIELD_MARKET_DESCRIPTION])
    return {
        "name": f"{owner}-{name}",
        "owner": {"name": owner},
        "metadata": {"description": marketplace_description},
        "plugins": [
            {
                "name": name,
                "source": "./",
                "description": first(skill[_MANIFEST().FIELD_DESCRIPTION]),
                "version": str(skill[_MANIFEST().FIELD_VERSION]),
            }
        ],
    }


def serialize(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def targets() -> list[tuple[Path, str]]:
    skill = read_json(MANIFEST_PATH)
    pkg = read_json(PACKAGE_PATH)
    return [
        (PLUGIN_PATH, serialize(build_plugin(skill, pkg))),
        (MARKETPLACE_PATH, serialize(build_marketplace(skill, pkg))),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate client plugin manifests from skill.manifest.json.")
    parser.add_argument("--write", action="store_true", help="write the generated manifests")
    parser.add_argument("--stdout", action="store_true", help="print the generated manifests and exit")
    args = parser.parse_args(argv)

    if not MANIFEST_PATH.exists():
        print(f"[error] missing {MANIFEST_PATH}", file=sys.stderr)
        return 1

    generated = targets()

    if args.stdout:
        for path, text in generated:
            print(f"===== {path.relative_to(ROOT).as_posix()} =====")
            print(text)
        return 0

    if args.write:
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        for path, text in generated:
            path.write_text(text, encoding="utf-8")
            print(f"[ok] wrote {path.relative_to(ROOT).as_posix()}")
        return 0

    drifted: list[str] = []
    for path, expected in generated:
        relative = path.relative_to(ROOT).as_posix()
        if not path.exists():
            drifted.append(f"{relative} (missing)")
        elif path.read_text(encoding="utf-8") != expected:
            drifted.append(f"{relative} (out of date)")

    if drifted:
        print("# Plugin Manifest Drift")
        print()
        for item in drifted:
            print(f"- {item}")
        print()
        print("Run: python devtools/gen_plugin_manifests.py --write")
        return 1

    print(f"Client plugin manifests are in sync with {MANIFEST_PATH.name} "
          f"(v{read_json(MANIFEST_PATH)['版本']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
