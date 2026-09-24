#!/usr/bin/env python3
"""skill.manifest.json 的**唯一解析入口**。

为什么需要这一层
================

`skill.manifest.json` 是全仓唯一的硬链接点：它的「版本 / 运行时文件 /
分发排除 / 宿主适配入口」被多处消费，历史上至少有 5 个消费方**各自**
`json.loads` 同一份文件。散落的解析带来两个具体问题：

1. **字段名硬编码散落**：中文键名（"运行时文件" 等）被写死在多个文件里，
   重命名或加字段时容易漏改。
2. **语义混装导致误判**：`分发排除` 曾被当作「永不发布」使用，而它实际上
   只约束 `.skill` / `.zip` 这一条通道 —— `bin/`、`lib/` 恰恰**要**进 npm。
   这次误判真的产生过一次错误告警（见下）。

因此本模块把「按通道解读排除规则」显式化，而不是让每个消费方自己猜。

分发通道语义（**关键区分**）
============================

本仓库有**两条互不相干的分发通道**，各自的边界不同：

===========================  ==========================================
通道                          边界来源
===========================  ==========================================
`.skill` / `.zip`（运行时分发）  manifest 的「运行时文件」白名单 + 「分发排除」
npm 包（`npm publish`）        `package.json` 的 `files` 白名单
===========================  ==========================================

- **npm 走白名单**：`files` 列出什么就发布什么。「分发排除」对它**没有任何
  影响**。所以 `bin/test-generator.js`、`lib/activation.js` 虽然在「分发排除」
  里（不进 .skill/.zip），但**必须**进 npm。
- **.skill/.zip 同时受两者影响**：白名单决定包内有什么，排除表负责清理
  白名单可能牵连到的产物。

由此得出**正确的判定规则**：判断某个 npm `files` 条目是否泄漏了本地/生成物，
**不能用「分发排除」**（那会误伤 bin/lib），而应当用 **`.gitignore`** ——
被 git 忽略的路径绝不该进任何发布物。

用法
====

    from manifest import load_manifest, runtime_files, distribution_excludes

    manifest = load_manifest()              # dict，缓存
    for path in runtime_files(): ...        # 已展开 "**" 通配
    for pattern in distribution_excludes(): ...

CLI（便于 shell 内联使用）：

    python devtools/manifest.py show
    python devtools/manifest.py version
    python devtools/manifest.py runtime-files
    python devtools/manifest.py excludes
    python devtools/manifest.py hosts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "skill.manifest.json"

# --- 字段名常量 ---------------------------------------------------------
# 集中定义，避免中文键名散落在多个文件里。
FIELD_NAME = "名称"
FIELD_DISPLAY_NAME = "显示名称"
FIELD_VERSION = "版本"
FIELD_ENTRY = "入口文件"
FIELD_DESCRIPTION = "说明"
FIELD_MARKET_DESCRIPTION = "市场说明"
FIELD_SCENARIOS = "适用场景"
FIELD_CAPABILITIES = "核心能力"
FIELD_RUNTIME_FILES = "运行时文件"
FIELD_HOST_ENTRIES = "宿主适配入口"
FIELD_EXCLUDES = "分发排除"
FIELD_PREFERRED_ARTIFACT = "推荐打包产物"
FIELD_COMPAT_ARTIFACT = "兼容打包产物"
FIELD_NPM_ENTRY = "Node.js安装入口"

# Node / 宿主侧键名（保持与 manifest 一致）
FIELD_NPM_PACKAGE = "npm包名"
FIELD_NPM_COMMAND = "命令"
FIELD_NPM_ENVIRONMENTS = "支持环境"

# 本地生成、**绝不入包**的产物片段。
# 纯通配展开（`dir/**`）会连带扫到它们；过滤掉才能让「运行时文件」清单
# 反映真实可分发内容。与 `.gitignore` 的判定保持一致。
LOCAL_ONLY_ARTIFACT_PATTERNS = (
    "__pycache__/",
    ".pyc",
    "knowledge/index.json",
    ".activated-files.json",
    ".DS_Store",
    "Thumbs.db",
)

_cache: dict[str, Any] | None = None


class ManifestError(RuntimeError):
    """manifest 缺失或不可解析。"""


def load_manifest(path: Path | None = None, *, use_cache: bool = True) -> dict:
    """读取并缓存 manifest。

    Args:
        path: 覆盖默认路径（测试用）。
        use_cache: 传 False 可强制重读（轮询或测试场景）。
    """
    global _cache
    if path is None and use_cache and _cache is not None:
        return _cache

    target = Path(path) if path else MANIFEST_PATH
    if not target.exists():
        raise ManifestError(f"missing manifest: {target}")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {target}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(f"manifest root must be an object, got {type(data).__name__}")

    if path is None:
        _cache = data
    return data


def clear_cache() -> None:
    """清空缓存（测试与长驻进程使用）。"""
    global _cache
    _cache = None


def _list_field(manifest: dict, field: str) -> List[str]:
    value = manifest.get(field) or []
    if not isinstance(value, list):
        raise ManifestError(f"field {field!r} must be a list, got {type(value).__name__}")
    return [str(v) for v in value]


def version(manifest: dict | None = None) -> str:
    """版本号 —— 全仓唯一数据源。"""
    return str((manifest or load_manifest()).get(FIELD_VERSION, "unknown"))


def runtime_files(manifest: dict | None = None) -> List[str]:
    """「运行时文件」原始条目（可能含 `**` / `*` 通配）。"""
    return _list_field(manifest or load_manifest(), FIELD_RUNTIME_FILES)


def host_entries(manifest: dict | None = None) -> dict[str, str]:
    """「宿主适配入口」：{宿主名: 相对路径}。"""
    value = (manifest or load_manifest()).get(FIELD_HOST_ENTRIES) or {}
    if not isinstance(value, dict):
        raise ManifestError(f"field {FIELD_HOST_ENTRIES!r} must be an object")
    return {str(k): str(v) for k, v in value.items()}


def distribution_excludes(manifest: dict | None = None) -> List[str]:
    """「分发排除」原始模式。

    **注意语义**：这只约束 `.skill` / `.zip` 通道（以及作为清理依据），
    **不是**「永不发布」。判定 npm 载荷请用 `.gitignore`，见模块 docstring。
    """
    return _list_field(manifest or load_manifest(), FIELD_EXCLUDES)


def npm_environments(manifest: dict | None = None) -> List[str]:
    """npm 激活入口声明的支持环境列表。"""
    entry = (manifest or load_manifest()).get(FIELD_NPM_ENTRY) or {}
    value = entry.get(FIELD_NPM_ENVIRONMENTS) or []
    return [str(v) for v in value]


def expand_runtime_entries(
    entries: Iterable[str] | None = None,
    *,
    root: Path | None = None,
) -> List[str]:
    """把「运行时文件」条目展开为**实际存在的文件**列表（相对仓库根的 POSIX 路径）。

    - 以 `/**` 结尾 → 递归收录该目录下所有文件
    - 是目录 → 递归收录
    - 是文件 → 原样收录
    - 不存在 → 跳过（是否算错误交给审计脚本判定，本函数只做展开）

    **已知本地产物会被过滤**（见 `LOCAL_ONLY_ARTIFACT_PATTERNS`）：纯通配
    （`dir/**`）在 git 工作区里会连带扫到 `__pycache__`、生成的
    `knowledge/index.json` 等。这些既不该进 distributable，也不该出现在
    「运行时文件实际都存在着」类审计的结果里 —— 否则审计会被噪声淹没。
    """
    base = Path(root) if root else ROOT
    patterns = list(entries) if entries is not None else runtime_files()
    # 与 lib/activation.js 的 collectRuntimeFiles 保持一致的隐式追加项
    patterns = patterns + ["DISTRIBUTION.md", "skill.manifest.json"]

    found: set[str] = set()
    for entry in patterns:
        if entry.endswith("/**"):
            directory = base / entry[: -len("/**")]
            for p in _walk_files(directory):
                found.add(_relative(base, p))
            continue

        target = base / entry
        if not target.exists():
            continue
        if target.is_dir():
            for p in _walk_files(target):
                found.add(_relative(base, p))
        else:
            found.add(_relative(base, target))

    return sorted(p for p in found if not is_local_only_artifact(p))


def is_local_only_artifact(relative_path: str) -> bool:
    """路径是否属于「本地生成、绝不入包」的产物。"""
    normalized = relative_path.replace("\\", "/")
    return any(pattern in normalized for pattern in LOCAL_ONLY_ARTIFACT_PATTERNS)


def _walk_files(directory: Path) -> List[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return [p for p in directory.rglob("*") if p.is_file()]


def _relative(base: Path, target: Path) -> str:
    return str(target.relative_to(base)).replace("\\", "/")


# --- CLI -----------------------------------------------------------------

def _cmd_show(manifest: dict, _args) -> int:
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def _cmd_version(manifest: dict, _args) -> int:
    print(version(manifest))
    return 0


def _cmd_runtime_files(manifest: dict, args) -> int:
    if args.expanded:
        for item in expand_runtime_entries(runtime_files(manifest)):
            print(item)
    else:
        for item in runtime_files(manifest):
            print(item)
    return 0


def _cmd_excludes(manifest: dict, _args) -> int:
    for item in distribution_excludes(manifest):
        print(item)
    return 0


def _cmd_hosts(manifest: dict, _args) -> int:
    for host, entry in sorted(host_entries(manifest).items()):
        print(f"{host}\t{entry}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manifest",
        description="skill.manifest.json 的唯一解析入口。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="输出完整 manifest JSON").set_defaults(func=_cmd_show)
    sub.add_parser("version", help="输出版本号").set_defaults(func=_cmd_version)

    p_runtime = sub.add_parser("runtime-files", help="输出运行时文件条目")
    p_runtime.add_argument("--expanded", action="store_true", help="展开通配为实际文件列表")
    p_runtime.set_defaults(func=_cmd_runtime_files)

    sub.add_parser("excludes", help="输出分发排除模式").set_defaults(func=_cmd_excludes)
    sub.add_parser("hosts", help="输出宿主适配入口").set_defaults(func=_cmd_hosts)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load_manifest()
    except ManifestError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return args.func(manifest, args)


if __name__ == "__main__":
    raise SystemExit(main())
