#!/usr/bin/env python3
"""文档结构层护栏：检查 testcase-generator 文档之间的一致性。

执行 10 类检查，输出 markdown 表格报告（pass / warn / fail 三档）：

1. 版本号三处一致：SKILL.md front matter / README.md 标题 / skill.manifest.json "版本"
2. 能力矩阵覆盖：skill.manifest.json 核心能力 ↔ SKILL.md ↔ prompts/phase*.md ↔ resources/output_artifacts.md
3. 宿主表三方一致：HOST_COMPATIBILITY.md ↔ adapters/ 实际目录 ↔ lib/activation.js 的 ENVIRONMENTS
4. npm 脚本入口：test-generator 命令在 README / package.json / HOST_COMPATIBILITY 都有提到
5. 运行时分发清单：skill.manifest.json "运行时文件" 实际都存在
6. 排他规则一致性：DISTRIBUTION.md "建议排除" ↔ skill.manifest.json "分发排除" ↔
   devtools/package_skill.py 的 STATIC_EXCLUDES + FORBIDDEN_ARCHIVE_PATTERNS
7. 版本↔changelog：当前 manifest 版本必须有对应的正式 changelog
8. docs/ 技能树路径：docs/ 引用技能内容时必须使用 skills/testcase-generator/ 前缀
9. docs/ 相对链接：docs/ 下的 Markdown 相对链接必须能解析到真实文件（SKILL.md 已随技能树迁移）
10. npm 发布载荷：package.json 的 files 目录条目不得牵连被 gitignore 的本地/生成物
11. 技能树内路径写法：技能树 Markdown 引用的 `knowledge/` 等顶层目录路径必须带 `<技能根>/` 前缀

设计原则：
- 不修改任何文件，只读不写
- 单一可信源：所有检查以"项目根目录"为锚点
- 中文输出，便于人读
- 支持 --format=json 便于 CI 集成
- 退出码：0 表示没有 fail；1 表示至少一个 fail
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable


# 仓库根目录：本脚本在 .harness/scripts/ 下，向上一级是仓库根
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
# 技能运行时内容的唯一位置（Agent Skills 标准布局）。
# 注意：`skills/` 是 canonical 源，**不是**镜像目录。
SKILL_DIR = "skills/testcase-generator"


def skill_path(relative: str) -> Path:
    """技能树内的路径（prompts / references / resources / templates / config / scripts / knowledge）。"""
    return ROOT / SKILL_DIR / relative


@dataclass
class CheckResult:
    """单条检查结果。"""

    name: str
    status: str  # pass / warn / fail
    detail: str
    extra: list[str] = field(default_factory=list)


# ---------- 工具函数 ----------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(read_text(path))
    except (json.JSONDecodeError, FileNotFoundError):
        return None


# ---------- 检查 1：版本号三处一致 ----------

# 匹配 front matter 中形如 `version: 2.1.0` 的行
FRONTMATTER_RE = re.compile(r"^---\s*$(.*?)^---\s*$", re.MULTILINE | re.DOTALL)
VERSION_LINE_RE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)

# 匹配 README 第一行 H1 中形如 `v2.1.0` 或 `2.1.0`
README_TITLE_RE = re.compile(
    r"^#\s+.+?v?(\d+\.\d+(?:\.\d+)?)\b",
    re.MULTILINE,
)


def extract_skill_md_version(skill_path: Path) -> str | None:
    """从 SKILL.md front matter 提取 version 字段。"""
    if not skill_path.exists():
        return None
    text = read_text(skill_path)
    fm_match = FRONTMATTER_RE.search(text)
    if not fm_match:
        return None
    fm_body = fm_match.group(1)
    ver_match = VERSION_LINE_RE.search(fm_body)
    return ver_match.group(1).strip() if ver_match else None


def extract_readme_version(readme_path: Path) -> str | None:
    """从 README.md 第一个 H1 提取版本号。"""
    if not readme_path.exists():
        return None
    text = read_text(readme_path)
    # 取第一个 H1
    first_h1 = re.search(r"^#\s+(.+?)$", text, re.MULTILINE)
    if not first_h1:
        return None
    title = first_h1.group(1)
    match = README_TITLE_RE.search("# " + title)  # 复用同样的正则
    return match.group(1).strip() if match else None


def extract_manifest_version(manifest_path: Path) -> str | None:
    """从 skill.manifest.json 提取 "版本" 字段。"""
    manifest = read_json(manifest_path)
    if not manifest:
        return None
    version = manifest.get("版本")
    return str(version) if version is not None else None


def normalize_version(version: str | None) -> str:
    """统一版本号格式：剥掉前导 'v'，处理 None。"""
    if not version:
        return ""
    return version.lstrip("v").strip()


def check_version_alignment() -> CheckResult:
    skill_entry = skill_path("SKILL.md")
    readme_path = ROOT / "README.md"
    manifest_path = ROOT / "skill.manifest.json"

    skill_v = extract_skill_md_version(skill_entry)
    readme_v = extract_readme_version(readme_path)
    manifest_v = extract_manifest_version(manifest_path)

    norm_skill = normalize_version(skill_v)
    norm_readme = normalize_version(readme_v)
    norm_manifest = normalize_version(manifest_v)

    extra = [
        f"SKILL.md front matter: {skill_v or 'NOT FOUND'}",
        f"README.md title: {readme_v or 'NOT FOUND'}",
        f"skill.manifest.json 版本: {manifest_v or 'NOT FOUND'}",
    ]

    # 任一缺失 → fail
    if not norm_skill:
        return CheckResult(
            "version_alignment",
            "fail",
            "SKILL.md front matter 中缺少 version 字段，无法参与对齐校验",
            extra,
        )
    if not norm_manifest:
        return CheckResult(
            "version_alignment",
            "fail",
            "skill.manifest.json 中缺少 版本 字段",
            extra,
        )
    if not norm_readme:
        return CheckResult(
            "version_alignment",
            "fail",
            "README.md 第一个 H1 标题中未找到版本号（形如 v2.1.0）",
            extra,
        )

    # 三处一致 → pass
    if norm_skill == norm_readme == norm_manifest:
        return CheckResult(
            "version_alignment",
            "pass",
            f"三处版本号一致：{norm_skill}",
            extra,
        )

    # 不一致 → fail
    return CheckResult(
        "version_alignment",
        "fail",
        f"三处版本号不一致：SKILL.md={norm_skill}, README.md={norm_readme}, manifest={norm_manifest}",
        extra,
    )


# ---------- 检查 2：能力矩阵覆盖 ----------

CORE_CAPABILITIES = [
    "输入质量预处理",
    "可测试需求抽取",
    "代码与接口契约辅助分析",
    "领域模型与状态模型构建",
    "MBT 导向测试设计",
    "结构化测试用例生成",
    "追溯矩阵与质量门禁",
]

# 6 个阶段 prompt 文件（相对技能树根）
PHASE_PROMPT_FILES = [
    f"{SKILL_DIR}/prompts/phase0_input_preprocessing_prompt.md",
    f"{SKILL_DIR}/prompts/phase1_requirements_prompt.md",
    f"{SKILL_DIR}/prompts/phase2_code_analysis_prompt.md",
    f"{SKILL_DIR}/prompts/phase3_domain_analysis_prompt.md",
    f"{SKILL_DIR}/prompts/phase4_mbt_design_prompt.md",
    f"{SKILL_DIR}/prompts/phase5_testcase_generation_prompt.md",
]


def check_capability_coverage() -> list[CheckResult]:
    """能力矩阵覆盖：核心能力在 SKILL.md / 至少一个 prompt / output_artifacts.md 都有提及。"""
    manifest = read_json(ROOT / "skill.manifest.json")
    declared = []
    if manifest:
        core = manifest.get("核心能力", {})
        declared = list(core.get("zh-CN", []))

    if not declared:
        return [
            CheckResult(
                "capability_coverage",
                "fail",
                "skill.manifest.json 中 核心能力.zh-CN 为空或缺失",
            )
        ]

    entry = skill_path("SKILL.md")
    skill_text = read_text(entry) if entry.exists() else ""
    artifacts = skill_path("resources/output_artifacts.md")
    output_artifacts_text = read_text(artifacts) if artifacts.exists() else ""
    phase_texts = []
    for rel in PHASE_PROMPT_FILES:
        p = ROOT / rel
        if p.exists():
            phase_texts.append((rel, read_text(p)))

    results = []
    missing_in_skill = []
    missing_in_artifacts = []
    missing_in_prompts = []
    for cap in declared:
        if cap not in skill_text:
            missing_in_skill.append(cap)
        if cap not in output_artifacts_text:
            missing_in_artifacts.append(cap)
        if not any(cap in t for _, t in phase_texts):
            missing_in_prompts.append((cap, "无任何 prompt 提及"))

    if missing_in_skill:
        results.append(
            CheckResult(
                "capability_in_skill_md",
                "fail",
                f"以下核心能力在 SKILL.md 中未提及：{', '.join(missing_in_skill)}",
                missing_in_skill,
            )
        )
    else:
        results.append(
            CheckResult(
                "capability_in_skill_md",
                "pass",
                f"SKILL.md 提及全部 {len(declared)} 项核心能力",
            )
        )

    if missing_in_artifacts:
        results.append(
            CheckResult(
                "capability_in_output_artifacts",
                "warn",
                f"以下核心能力在 resources/output_artifacts.md 中未提及：{', '.join(missing_in_artifacts)}",
                missing_in_artifacts,
            )
        )
    else:
        results.append(
            CheckResult(
                "capability_in_output_artifacts",
                "pass",
                f"resources/output_artifacts.md 提及全部 {len(declared)} 项核心能力",
            )
        )

    if missing_in_prompts:
        caps = [c for c, _ in missing_in_prompts]
        results.append(
            CheckResult(
                "capability_in_prompts",
                "warn",
                f"以下核心能力无任何 prompts/phase*.md 提及：{', '.join(caps)}",
                caps,
            )
        )
    else:
        results.append(
            CheckResult(
                "capability_in_prompts",
                "pass",
                "全部核心能力至少被一个 prompts/phase*.md 提及",
            )
        )

    return results


# ---------- 检查 3：宿主表三方一致 ----------

# 从 `| 宿主 | ...` 表格行提取第一列（宿主名）
HOST_TABLE_ROW_RE = re.compile(
    r"^\|\s*([a-zA-Z][\w-]*)\s*\|",
    re.MULTILINE,
)


# 匹配 markdown 表格行第一个 cell：`| 名称 | ...`
TABLE_CELL_RE = re.compile(r"^\|\s*`?([^`|\r\n]+?)`?\s*\|")
SECTION_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# 不应作为宿主名出现在第一列的固定表头词
TABLE_HEADER_DENYLIST = {
    "宿主", "环境名", "语言策略", "推荐程度", "路径", "默认本地目标目录",
    "额外入口", "入口文件", "排除原因", "当前路径", "建议长期位置",
    "说明", "用途", "特性", "阶段", "名称", "目标", "常见产物",
}


def parse_table_section(text: str, section_titles: Iterable[str]) -> list[str]:
    """从 markdown 文本中匹配章节标题（任意一个），提取章节内表格第一列。"""
    sections = list(SECTION_HEADER_RE.finditer(text))
    captured: list[str] = []
    titles_norm = {t.strip() for t in section_titles}
    for idx, match in enumerate(sections):
        title = match.group(1).strip()
        if title not in titles_norm:
            continue
        start = match.end()
        end = sections[idx + 1].start() if idx + 1 < len(sections) else len(text)
        section_text = text[start:end]
        for line in section_text.splitlines():
            m = TABLE_CELL_RE.match(line)
            if not m:
                continue
            cell = m.group(1).strip()
            if not cell or cell in TABLE_HEADER_DENYLIST or set(cell) <= {"-"}:
                continue
            captured.append(cell)
    return captured


def extract_hosts_from_host_compatibility() -> list[str]:
    """从 HOST_COMPATIBILITY.md 的宿主适配入口表 + Node.js 激活入口表提取宿主名。

    返回所有出现的宿主原始字符串。
    """
    path = ROOT / "HOST_COMPATIBILITY.md"
    if not path.exists():
        return []
    text = read_text(path)
    # 两张表都会涉及宿主
    cells = parse_table_section(
        text,
        ["宿主适配入口", "Node.js 激活入口"],
    )
    return cells


def extract_hosts_from_adapters_dir() -> list[str]:
    """从 adapters/ 实际子目录提取宿主名。"""
    adapters = ROOT / "adapters"
    if not adapters.exists():
        return []
    return sorted(p.name for p in adapters.iterdir() if p.is_dir())


def extract_hosts_from_activation_js() -> list[str]:
    """从 lib/activation.js 提取 ENVIRONMENTS 的顶层键（不包含嵌套 entry 等）。"""
    path = ROOT / "lib/activation.js"
    if not path.exists():
        return []
    text = read_text(path)
    # 匹配 `const ENVIRONMENTS = { ... }` 块
    match = re.search(
        r"const\s+ENVIRONMENTS\s*=\s*\{",
        text,
    )
    if not match:
        return []
    # 从匹配位置开始扫描，跟踪花括号深度
    start = match.end() - 1  # 指向 `{`
    depth = 0
    keys: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        elif depth == 1:
            # 在顶层（depth == 1 表示在 ENVIRONMENTS 的直接子层）
            m = re.match(r"\s*([a-zA-Z][\w-]*)\s*:\s*\{", text[i:])
            if m:
                keys.append(m.group(1))
                # 跳过本键对应的子对象（找到匹配的 `}`）
                sub_depth = 1
                j = i + m.end()
                while j < len(text) and sub_depth > 0:
                    if text[j] == "{":
                        sub_depth += 1
                    elif text[j] == "}":
                        sub_depth -= 1
                    j += 1
                i = j
                continue
        i += 1
    return keys


# 宿主显示名 -> ENVIRONMENTS 键的显式映射（只在「取第一个英文词」会取错时才需要）。
# 例如 "Google Antigravity" 的首词是 Google、"Command Code" 的首词是 Command、
# "Factory Droid" 的首词是 Factory —— 都不是真正的环境键，必须显式纠正。
HOST_NAME_PREFIX_OVERRIDES = {
    "google": "antigravity",
    "command": "commandcode",
    "factory": "droid",
    "github": "githubcopilot",
    "kilo": "kilocode",
}

# 提取 cell 中的英文 token（忽略大小写）时使用的正则。
_ENGLISH_TOKEN_RE = re.compile(r"[A-Za-z][\w-]*")
# 裸英文键判定。
_BARE_KEY_RE = re.compile(r"^[a-z][a-z0-9]*$")


def normalize_host_name(cell: str) -> str:
    """把 HOST_COMPATIBILITY.md 表格里的中文/混合名称规整为 ENVIRONMENTS 中使用的英文小写键。

    规则（按优先级）：
    1. 裸英文小写（直接是 `claude`、`codex`、`githubcopilot` 等）——原样返回。
    2. 取第一个英文 token 并小写；若它命中 PREFIX_OVERRIDES，替换为真正的键。
       这一步**必须**在「token 本身像键」判定之前 —— 否则 "Google Antigravity"
       的首词 "Google" 会被当成合法键直接返回。
    3. 否则取**第一个本身就像合法键**的英文 token（覆盖 "OpenHands"、"Clawdbot"、
       "MCPJam" 这类「驼峰拼成一个词」、且首词并非真实键的名字）。
    4. 都失败则原样返回小写。

    历史上这里「无条件取第一个 token 小写」会在带厂商前缀的显示名上取错词
    （Google Antigravity -> google），所以引入 2/3 的逐级收敛。
    """
    cell = cell.strip()
    # 1. 直接是裸英文键
    if _BARE_KEY_RE.match(cell):
        return cell
    tokens = _ENGLISH_TOKEN_RE.findall(cell)
    if not tokens:
        return cell.lower()
    # 2. 首词的厂商前缀别名优先
    first = tokens[0].lower()
    if first in HOST_NAME_PREFIX_OVERRIDES:
        return HOST_NAME_PREFIX_OVERRIDES[first]
    # 3. 第一个本身就像合法键的 token
    for token in tokens:
        lowered = token.lower()
        if _BARE_KEY_RE.match(lowered):
            return lowered
    return first


def check_host_table_consistency() -> list[CheckResult]:
    raw_doc = extract_hosts_from_host_compatibility()
    from_adapters = extract_hosts_from_adapters_dir()
    from_activation = extract_hosts_from_activation_js()

    # 规范化宿主表中的中文/混合名为英文小写键
    normalized_doc: set[str] = set()
    for cell in raw_doc:
        norm = normalize_host_name(cell)
        if norm and re.match(r"^[a-z][\w-]*$", norm):
            normalized_doc.add(norm)

    set_adapter = set(from_adapters)
    set_activation = set(from_activation)

    results = []

    if not set_activation:
        results.append(
            CheckResult(
                "host_table_consistency",
                "fail",
                "lib/activation.js 中未找到 ENVIRONMENTS 常量",
            )
        )
        return results

    in_doc_not_in_activation = normalized_doc - set_activation
    in_activation_not_in_doc = set_activation - normalized_doc
    in_adapter_not_in_activation = set_adapter - set_activation
    in_activation_not_in_adapter = set_activation - set_adapter

    if in_doc_not_in_activation:
        results.append(
            CheckResult(
                "host_doc_vs_activation",
                "warn",
                f"HOST_COMPATIBILITY.md 提到但 ENVIRONMENTS 未注册：{', '.join(sorted(in_doc_not_in_activation))}",
                sorted(in_doc_not_in_activation),
            )
        )

    if in_activation_not_in_doc:
        results.append(
            CheckResult(
                "host_activation_vs_doc",
                "fail",
                f"ENVIRONMENTS 已注册但 HOST_COMPATIBILITY.md 未提及：{', '.join(sorted(in_activation_not_in_doc))}",
                sorted(in_activation_not_in_doc),
            )
        )

    if in_adapter_not_in_activation:
        results.append(
            CheckResult(
                "host_adapter_vs_activation",
                "fail",
                f"adapters/ 子目录存在但 ENVIRONMENTS 未注册：{', '.join(sorted(in_adapter_not_in_activation))}",
                sorted(in_adapter_not_in_activation),
            )
        )

    if in_activation_not_in_adapter:
        results.append(
            CheckResult(
                "host_activation_vs_adapter",
                "warn",
                f"ENVIRONMENTS 已注册但 adapters/ 缺少入口目录：{', '.join(sorted(in_activation_not_in_adapter))}",
                sorted(in_activation_not_in_adapter),
            )
        )

    if not results:
        results.append(
            CheckResult(
                "host_table_consistency",
                "pass",
                f"HOST_COMPATIBILITY.md / adapters/ / ENVIRONMENTS 三方一致：{', '.join(sorted(set_activation))}",
            )
        )

    return results


# ---------- 检查 4：npm 脚本入口 ----------

def check_npm_entrypoint() -> list[CheckResult]:
    """test-generator 命令在 README / package.json / HOST_COMPATIBILITY 都有提到。"""
    results = []

    # package.json
    pkg = read_json(ROOT / "package.json")
    pkg_bin_keys = list((pkg or {}).get("bin", {}).keys()) if pkg else []

    if not pkg_bin_keys:
        results.append(
            CheckResult(
                "npm_entrypoint_in_package_json",
                "fail",
                "package.json 中缺少 bin 字段",
            )
        )
    elif "test-generator" not in pkg_bin_keys:
        results.append(
            CheckResult(
                "npm_entrypoint_in_package_json",
                "fail",
                f"package.json 的 bin 中未注册 test-generator，实际：{', '.join(pkg_bin_keys)}",
            )
        )
    else:
        results.append(
            CheckResult(
                "npm_entrypoint_in_package_json",
                "pass",
                "package.json 的 bin 中注册了 test-generator",
            )
        )

    # README.md
    readme_text = read_text(ROOT / "README.md") if (ROOT / "README.md").exists() else ""
    if "test-generator" in readme_text:
        results.append(
            CheckResult(
                "npm_entrypoint_in_readme",
                "pass",
                "README.md 中提到了 test-generator 命令",
            )
        )
    else:
        results.append(
            CheckResult(
                "npm_entrypoint_in_readme",
                "fail",
                "README.md 中未提到 test-generator 命令",
            )
        )

    # HOST_COMPATIBILITY.md
    hc_text = (
        read_text(ROOT / "HOST_COMPATIBILITY.md")
        if (ROOT / "HOST_COMPATIBILITY.md").exists()
        else ""
    )
    if "test-generator" in hc_text:
        results.append(
            CheckResult(
                "npm_entrypoint_in_host_compatibility",
                "pass",
                "HOST_COMPATIBILITY.md 中提到了 test-generator 命令",
            )
        )
    else:
        results.append(
            CheckResult(
                "npm_entrypoint_in_host_compatibility",
                "fail",
                "HOST_COMPATIBILITY.md 中未提到 test-generator 命令",
            )
        )

    return results


# ---------- 检查 5：运行时分发清单 ----------

def check_runtime_files_exist() -> list[CheckResult]:
    """skill.manifest.json 的"运行时文件"列出的文件/目录实际都存在。"""
    manifest = read_json(ROOT / "skill.manifest.json")
    if not manifest:
        return [
            CheckResult(
                "runtime_files_exist",
                "fail",
                "skill.manifest.json 缺失或不是合法 JSON",
            )
        ]
    runtime_files = _manifest_module().runtime_files(manifest)
    if not runtime_files:
        return [
            CheckResult(
                "runtime_files_exist",
                "warn",
                "skill.manifest.json 中 运行时文件 为空",
            )
        ]

    missing = []
    for entry in runtime_files:
        # 处理 "dir/**" 这种 glob 形式
        if entry.endswith("/**"):
            base = entry[:-3]
            if not (ROOT / base).is_dir():
                missing.append(entry)
            continue
        # 普通文件
        if not (ROOT / entry).exists():
            missing.append(entry)

    if missing:
        return [
            CheckResult(
                "runtime_files_exist",
                "fail",
                f"以下运行时文件/目录不存在：{', '.join(missing)}",
                missing,
            )
        ]
    return [
        CheckResult(
            "runtime_files_exist",
            "pass",
            f"全部 {len(runtime_files)} 个运行时条目存在",
        )
    ]


# ---------- 检查 6：排他规则一致性 ----------

# DISTRIBUTION.md "建议排除" 表的路径形如 `| `path/` | reason |`
DIST_EXCLUDES_RE = re.compile(r"^\|\s*`?([^`|\s]+(?:\*\*)?)`?\s*\|", re.MULTILINE)


def extract_excludes_from_distribution_md() -> list[str]:
    """从 DISTRIBUTION.md 的"建议排除"和"开发工具处理"表格提取路径。

    两个章节都会列出"应排除/不进包"的路径，本函数汇总两者。
    """
    path = ROOT / "DISTRIBUTION.md"
    if not path.exists():
        return []
    text = read_text(path)
    cells = parse_table_section(
        text,
        ["建议排除", "开发工具处理"],
    )
    return cells


def _manifest_module():
    """惰性导入 devtools/manifest.py —— manifest 的唯一解析入口。"""
    devtools_dir = ROOT / "devtools"
    if str(devtools_dir) not in sys.path:
        sys.path.insert(0, str(devtools_dir))
    import manifest as manifest_module  # noqa: PLC0415

    return manifest_module


def extract_excludes_from_manifest() -> list[str]:
    """从 skill.manifest.json 的"分发排除"数组提取（经 devtools/manifest.py 统一解析）。"""
    manifest = read_json(ROOT / "skill.manifest.json")
    if not manifest:
        return []
    return list(_manifest_module().distribution_excludes(manifest))


def extract_excludes_from_package_skill() -> tuple[set[str], set[str]]:
    """从 devtools/package_skill.py 提取 STATIC_EXCLUDES 和 FORBIDDEN_ARCHIVE_PATTERNS。

    使用 ast 解析常量赋值，精确取出。
    """
    path = ROOT / "devtools" / "package_skill.py"
    static: set[str] = set()
    forbidden: set[str] = set()

    if not path.exists():
        return static, forbidden

    try:
        tree = ast.parse(read_text(path))
    except SyntaxError:
        return static, forbidden

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            value = node.value
            if isinstance(value, ast.Set):
                elements = {ast.literal_eval(elt) for elt in value.elts if isinstance(elt, ast.Constant)}
                if name == "STATIC_EXCLUDES":
                    static = {str(e) for e in elements}
                elif name == "FORBIDDEN_ARCHIVE_PATTERNS":
                    forbidden = {str(e) for e in elements}
    return static, forbidden


def normalize_exclude_path(p: str) -> str:
    """统一排除路径的格式：剥掉 "/**" 后缀、尾部斜杠，但保留前导点（重要：".claude" != "claude"）。

    - `".claude/**"` → `".claude"`
    - `"test-output/**"` → `"test-output"`
    - `"testcase-generator.skill"` → `"testcase-generator.skill"`（glob 在归一化时保留）
    - `"./claude/"` → `"./claude"`（保留相对前缀）

    glob 模式 (`*.skill`, `*.zip`) 不会被改动。
    """
    p = p.strip()
    # 只去尾部斜杠
    p = p.rstrip("/")
    if p.endswith("/**"):
        p = p[:-3]
    return p


def check_excludes_consistency() -> list[CheckResult]:
    """DISTRIBUTION.md "建议排除" / "开发工具处理" ↔ manifest "分发排除" ↔ package_skill.py 常量。"""
    from_dist = {normalize_exclude_path(p) for p in extract_excludes_from_distribution_md()}
    from_manifest = {normalize_exclude_path(p) for p in extract_excludes_from_manifest()}
    static, forbidden = extract_excludes_from_package_skill()
    # STATIC_EXCLUDES 是个简单的目录名集合，不带斜杠
    static_normalized = {normalize_exclude_path(p) for p in static}
    forbidden_normalized = {normalize_exclude_path(p) for p in forbidden}
    # 保留 glob 模式原样（用于 critical_paths 匹配）
    forbidden_patterns = set(forbidden)

    results = []

    # 1. manifest ↔ DISTRIBUTION.md
    in_manifest_not_in_dist = from_manifest - from_dist
    in_dist_not_in_manifest = from_dist - from_manifest

    if in_manifest_not_in_dist:
        results.append(
            CheckResult(
                "manifest_excludes_vs_distribution",
                "warn",
                f"manifest 分发排除中存在但 DISTRIBUTION.md 建议排除/开发工具表未列出：{', '.join(sorted(in_manifest_not_in_dist))}",
                sorted(in_manifest_not_in_dist),
            )
        )
    if in_dist_not_in_manifest:
        results.append(
            CheckResult(
                "distribution_excludes_vs_manifest",
                "warn",
                f"DISTRIBUTION.md 建议排除表存在但 manifest 分发排除中未列出：{', '.join(sorted(in_dist_not_in_manifest))}",
                sorted(in_dist_not_in_manifest),
            )
        )
    if not in_manifest_not_in_dist and not in_dist_not_in_manifest:
        results.append(
            CheckResult(
                "manifest_excludes_consistency",
                "pass",
                f"manifest 分发排除 与 DISTRIBUTION.md 建议排除/开发工具表 一致（共 {len(from_manifest)} 项）",
            )
        )

    # 2. manifest ↔ package_skill.py 关键禁入项
    # 关键路径 = 必须被禁止的目录/文件/glob
    # 对每个关键项，检查它是否被 package_skill 的 STATIC_EXCLUDES / FORBIDDEN_ARCHIVE_PATTERNS 覆盖
    # 覆盖规则：精确包含、glob 匹配 (e.g. *.skill 覆盖 testcase-generator.skill)
    def is_covered(item: str, static_set: set[str], forbidden_set: set[str]) -> bool:
        if item in static_set or item in forbidden_set:
            return True
        from fnmatch import fnmatch
        for pat in forbidden_set:
            if fnmatch(item, pat):
                return True
        return False

    # 关键禁入路径集合（铁律 4.1 + 实际多宿主列表）
    critical_paths = {
        # 多宿主镜像目录
        ".claude", ".qoder", ".trae", ".agents", ".workbuddy",
        ".codebuddy", ".cursor", ".windsurf",
        # 本地验证产物
        # 注意：`skills` 不在此列 —— 它是 canonical 技能树，必须入包。
        "test-output", "skills-lock.json",
        # 包中包
        "testcase-generator.skill", "testcase-generator.zip",
        # 开发工具
        "devtools", "PACKAGING.md", "run_package.bat",
    }
    pkg_combined = static_normalized | forbidden_normalized
    missing_in_pkg = sorted(
        p for p in critical_paths if not is_covered(p, static_normalized, forbidden_normalized)
    )
    if missing_in_pkg:
        results.append(
            CheckResult(
                "package_skill_forbidden_critical",
                "fail",
                f"以下关键禁入项在 devtools/package_skill.py 中未声明：{', '.join(missing_in_pkg)}",
                missing_in_pkg,
            )
        )
    else:
        results.append(
            CheckResult(
                "package_skill_forbidden_critical",
                "pass",
                f"devtools/package_skill.py 已声明全部 {len(critical_paths)} 个关键禁入项",
            )
        )

    # 3. package_skill.py 静态排除 vs manifest 排除
    # STATIC_EXCLUDES 里的项如果不在 manifest 里，也应 warn
    extra_static = static_normalized - from_manifest
    if extra_static:
        # 过滤掉一些已知的合理差异（如 __pycache__, .DS_Store, run_package.bat）
        ignorable = {"__pycache__", ".DS_Store", "run_package.bat", "PACKAGING.md"}
        filtered = sorted(extra_static - ignorable)
        if filtered:
            results.append(
                CheckResult(
                    "package_skill_static_vs_manifest",
                    "warn",
                    f"package_skill.py STATIC_EXCLUDES 包含但 manifest 未列出的项：{', '.join(filtered)}",
                    filtered,
                )
            )

    return results


# ---------- 检查 7：当前版本必须有正式 changelog ----------

def check_changelog_exists() -> CheckResult:
    """当前版本必须在 .harness/changelogs/ 下有正式 changelog。

    防止"版本号升了但发版日志没回填" —— v2.2.0 曾经长期停留在占位模板，
    而三处版本号一致性检查完全无法发现这一点。
    """
    manifest = read_json(ROOT / "skill.manifest.json")
    if not manifest:
        return CheckResult("changelog_exists", "fail", "无法读取 skill.manifest.json 以确定当前版本")

    version = str(manifest.get("版本", "")).strip()
    if not version:
        return CheckResult("changelog_exists", "fail", "skill.manifest.json 缺少 版本 字段")

    changelog_dir = ROOT / ".harness" / "changelogs"
    official = changelog_dir / f"v{version}.md"
    if official.is_file():
        return CheckResult(
            "changelog_exists",
            "pass",
            f"v{version} 的正式 changelog 已回填（.harness/changelogs/v{version}.md）",
        )

    placeholders = [
        name
        for name in (f"v{version}-TEMPLATE.md", f"v{version}-draft.md")
        if (changelog_dir / name).is_file()
    ]
    hint = f"；当前只找到 {'、'.join(placeholders)}" if placeholders else ""
    return CheckResult(
        "changelog_exists",
        "fail",
        f"找不到 .harness/changelogs/v{version}.md —— 当前版本未回填发版日志{hint}",
    )


# ---------- 检查 8：docs/ 中的技能树路径引用 ----------

# 技能树内的顶层目录。docs/ 里若引用这些目录下的文件，路径必须带 SKILL_DIR 前缀。
SKILL_TREE_DIRS = (
    "config", "knowledge", "prompts", "references", "resources", "scripts", "templates",
)

_DIR_ALT = "|".join(SKILL_TREE_DIRS)
# 已带正确前缀的引用不再重复判定，否则修好之后还会被反复报出来。
_GUARD = rf"(?<!{re.escape(SKILL_DIR)}/)"

# 文件级引用：`resources/output_artifacts.md`
SKILL_TREE_TOKEN_RE = re.compile(_GUARD + rf"`?((?:{_DIR_ALT})/[A-Za-z0-9_./-]+)`?")

# 通配 / 占位引用：`templates/*.md`、`knowledge/sources/<slug>.md`、`resources/*`
#
# **只在 `dir/` 后面紧跟通配符或占位符时才判定**。刻意不匹配裸目录名（如 `prompts/`）：
# 对标报告一类文档会用裸目录名描述**其他项目**的布局（Agent Skills 标准本身就含
# `scripts/` / `references/` / `assets/`），给它们加本项目的技能树前缀会是错的。
# 而后接 `*` 或 `<` 必然是"某个具体文件的通配写法"，不存在这种歧义。
SKILL_TREE_DIR_RE = re.compile(_GUARD + rf"`?((?:{_DIR_ALT})/)(?=[*<])`?")

# Markdown 相对链接。`SKILL.md` 也随技能树迁移了，因此它只作为链接目标时才算路径
# —— 正文里把 "SKILL.md" 当概念提到的场合很多，不能按路径判失效。
MARKDOWN_LINK_RE = re.compile(r"\]\((?P<url>[^)\s]+)\)")

# 行内代码段。检查链接前先把它屏蔽掉 —— 否则"解释 Markdown 语法"的文档
# （例如正文里写 `` `](url)` ``）会被自己的检查当成真链接。
CODE_SPAN_RE = re.compile(r"`[^`]*`")


def mask_code_spans(line: str) -> str:
    """把行内代码段替换为等长空白，保持其余内容与列位置不变。"""
    return CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), line)


def find_broken_docs_links() -> list[str]:
    """返回 docs/ 下无法解析的相对链接（`file:line → url`）。"""
    broken: list[str] = []
    docs_root = ROOT / "docs"
    if not docs_root.is_dir():
        return broken

    for path in sorted(docs_root.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(read_text(path).splitlines(), 1):
            for match in MARKDOWN_LINK_RE.finditer(mask_code_spans(line)):
                url = match.group("url").split("#", 1)[0].strip()
                if not url or url.startswith(("http://", "https://", "mailto:", "file://")):
                    continue
                if not (path.parent / url).exists():
                    broken.append(f"{relative}:{lineno} → {url}")

    return broken


def find_stale_docs_paths() -> list[str]:
    """返回 docs/ 下指向技能树、却仍写成根级路径的引用（`file:line → token`）。"""
    stale: list[str] = []
    docs_root = ROOT / "docs"
    if not docs_root.is_dir():
        return stale

    def misplaced(token: str) -> bool:
        """技能树下有、仓库根没有 —— 只在这种确定的情况下判为失效。"""
        return (ROOT / SKILL_DIR / token).exists() and not (ROOT / token).exists()

    for path in sorted(docs_root.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(read_text(path).splitlines(), 1):
            seen: set[str] = set()
            for pattern in (SKILL_TREE_TOKEN_RE, SKILL_TREE_DIR_RE):
                for match in pattern.finditer(line):
                    token = match.group(1).rstrip(".,;:、。")
                    if token in seen or not misplaced(token):
                        continue
                    seen.add(token)
                    stale.append(f"{relative}:{lineno} → {token}")

    return stale


def check_docs_skill_tree_paths() -> CheckResult:
    """docs/ 必须以技能树路径引用技能内容。

    判定是**零猜测**的：只有当"该文件在技能树下存在、且在仓库根不存在"时才算失效
    —— 因此不会误报分析性文字（例如对标报告里描述生态布局的 `prompts/`）。
    这一项是针对 P1-4 迁移遗漏 78 处 `docs/` 引用的回归守卫。
    """
    docs_root = ROOT / "docs"
    scanned = len(list(docs_root.rglob("*.md"))) if docs_root.is_dir() else 0
    stale = find_stale_docs_paths()

    if not stale:
        return CheckResult(
            "docs_skill_tree_paths",
            "pass",
            f"docs/ 下技能树路径引用均带 {SKILL_DIR}/ 前缀（已扫描 {scanned} 个文档）",
        )

    preview = "；".join(stale[:3])
    more = f"（另有 {len(stale) - 3} 处）" if len(stale) > 3 else ""
    return CheckResult(
        "docs_skill_tree_paths",
        "fail",
        f"docs/ 中存在 {len(stale)} 处失效的技能树路径引用：{preview}{more}",
        stale,
    )


def check_docs_markdown_links() -> CheckResult:
    """docs/ 下的相对链接必须能解析到真实文件。

    与 `check_docs_skill_tree_paths` 互补：后者管"路径写法"，本项管"链接是否可达"。
    `SKILL.md` 迁入技能树后曾留下 4 个指向 `../../SKILL.md` 的死链，正是本项要拦的。
    """
    docs_root = ROOT / "docs"
    scanned = len(list(docs_root.rglob("*.md"))) if docs_root.is_dir() else 0
    broken = find_broken_docs_links()

    if not broken:
        return CheckResult(
            "docs_markdown_links",
            "pass",
            f"docs/ 下相对链接均可解析（已扫描 {scanned} 个文档）",
        )

    preview = "；".join(broken[:3])
    more = f"（另有 {len(broken) - 3} 处）" if len(broken) > 3 else ""
    return CheckResult(
        "docs_markdown_links",
        "fail",
        f"docs/ 中存在 {len(broken)} 个失效的相对链接：{preview}{more}",
        broken,
    )


# ---------- 检查 10：npm 发布载荷 ----------

def ignored_by_git(paths: list[str]) -> set[str]:
    """返回其中被 git 忽略的路径（相对仓库根）。git 不可用时返回空集。"""
    if not paths or shutil.which("git") is None:
        return set()
    try:
        # 刻意用字节模式：text=True 会把写入子进程的 "\n" 转成 os.linesep，
        # 在 Windows 上会让 git 收到带 "\r" 的路径，输出也随之变脏。
        proc = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=ROOT,
            input=("\n".join(paths) + "\n").encode("utf-8"),
            capture_output=True,
        )
    except OSError:
        return set()
    # 退出码 1 表示"没有任何路径被忽略"，属正常情况
    output = proc.stdout.decode("utf-8", errors="replace")
    return {line.strip() for line in output.splitlines() if line.strip()}


def check_npm_files_payload() -> CheckResult:
    """`package.json` 的 `files` 不得把被 gitignore 的内容带进 npm 包。

    `files` 是白名单，但**一旦列出目录，该目录下所有内容都会进包** —— 实测确认
    `.npmignore` 对它无效（`__pycache__/`、`*.pyc`、本地构建的
    `knowledge/index.json` 都会被静默发布，曾占发布体积的 75%）。

    判定以 `.gitignore` 为单一可信源：**凡被 git 忽略的路径都是本地/生成物，
    绝不该出现在发布包里**。这样既覆盖 Python 缓存这类通用产物，也覆盖项目自有的
    构建产物，无需在审计里硬编码清单，也不会误伤"该进 npm 但不进 .skill/.zip"
    的运行时文件（如 `bin/`、`lib/` —— 它们并未被忽略）。
    """
    pkg = read_json(ROOT / "package.json")
    entries = list(pkg.get("files") or [])
    if not entries:
        return CheckResult(
            "npm_files_payload", "warn", "package.json 未声明 files，npm 将回落到 .gitignore 规则"
        )

    problems: list[str] = []
    candidates: list[str] = []
    dir_owner: dict[str, str] = {}

    for entry in entries:
        hits = sorted(ROOT.glob(entry))
        if not hits:
            problems.append(f"{entry}（未匹配到任何文件）")
            continue
        # 通配条目只能匹配指定形态，不可能牵连产物
        if any(ch in entry for ch in "*?["):
            continue
        for hit in hits:
            if not hit.is_dir():
                continue
            for path in hit.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT).as_posix()
                candidates.append(relative)
                dir_owner[relative] = entry

    for relative in sorted(ignored_by_git(candidates)):
        problems.append(f"{dir_owner.get(relative, '?')}/ 牵连 {relative}（被 .gitignore 排除）")

    if problems:
        preview = "；".join(problems[:4])
        more = f"（另有 {len(problems) - 4} 处）" if len(problems) > 4 else ""
        return CheckResult(
            "npm_files_payload",
            "fail",
            f"package.json 的 files 目录条目会把 gitignore 的本地/生成物打进 npm 包：{preview}{more}",
            problems,
        )

    return CheckResult(
        "npm_files_payload",
        "pass",
        f"package.json 的 {len(entries)} 个 files 条目未牵连被 gitignore 的内容",
    )


# ---------- 检查 11：技能树内的路径写法 ----------

# 技能树顶层目录：技能树内的文档若引用它们，必须带 `<技能根>/` 前缀。
# 与检查 8 的区别：检查 8 管 docs/ 里引用技能树（要补 skills/testcase-generator/），
# 本项管技能树内部自引用（要补 `<技能根>/` 占位符）。
SKILL_INTERNAL_DIRS = (
    "config", "knowledge", "prompts", "references", "resources", "scripts", "templates",
)

_SKILL_DIR_ALT = "|".join(SKILL_INTERNAL_DIRS)
# 已带 `<技能根>/` 前缀的不再判定。
_SKILL_INTERNAL_GUARD = rf"(?<!{re.escape('<技能根>/')})"

# 文件级引用：`knowledge/scripts/search.py`、`prompts/phase1_requirements_prompt.md`
SKILL_INTERNAL_TOKEN_RE = re.compile(
    _SKILL_INTERNAL_GUARD + rf"`?((?:{_SKILL_DIR_ALT})/[A-Za-z0-9_./-]+)`?"
)

# 通配 / 占位引用：`knowledge/sources/*.md`、`knowledge/sources/<slug>.md`
SKILL_INTERNAL_DIR_RE = re.compile(
    _SKILL_INTERNAL_GUARD + rf"`?((?:{_SKILL_DIR_ALT})/)(?=[*<])`?"
)

# Markdown 链接目标（`](../../prompts/x.md)`）在技能树内是合法的相对写法，
# 不应被前缀规则误伤。扫描前先屏蔽行内代码与链接目标。
_MD_LINK_TARGET_RE = re.compile(r"\]\([^)\s]+\)")


def mask_non_path_spans(line: str) -> str:
    """屏蔽行内代码段与 Markdown 链接目标，避免对它们套用路径前缀规则。"""
    masked = _MD_LINK_TARGET_RE.sub(lambda m: " " * len(m.group(0)), line)
    return mask_code_spans(masked)


def find_skill_tree_bare_paths() -> list[str]:
    """返回技能树内未带 `<技能根>/` 前缀的顶层目录路径引用（`file:line → token`）。

    判定是**零猜测**的：只有当"该路径在技能树下真实存在"时才算失效
    —— 因此不会误报分析性文字（如对标报告里描述其他项目布局的 `scripts/`）。
    `knowledge/` 既作目录树标签又作路径前缀，故对**目录名单独成行**的树标签
    放行（详见 `_is_tree_label`）。
    """
    stale: list[str] = []
    skill_root = ROOT / SKILL_DIR
    if not skill_root.is_dir():
        return stale

    def exists_in_skill(token: str) -> bool:
        return (skill_root / token).exists()

    for path in sorted(skill_root.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(read_text(path).splitlines(), 1):
            masked = mask_non_path_spans(line)
            seen: set[str] = set()
            for pattern in (SKILL_INTERNAL_TOKEN_RE, SKILL_INTERNAL_DIR_RE):
                for match in pattern.finditer(masked):
                    token = match.group(1).rstrip(".,;:、。")
                    if token in seen or not exists_in_skill(token):
                        continue
                    seen.add(token)
                    stale.append(f"{relative}:{lineno} → {token}")

    return stale


def check_skill_tree_internal_paths() -> CheckResult:
    """技能树内的路径引用必须带 `<技能根>/` 前缀。

    技能树的各个子目录处于**不同深度**（`knowledge/README.md` 在知识库内，
    `references/` 与 `prompts/` 是同级兄弟），同一串 `knowledge/scripts/x.py`
    在不同文件里指向的相对位置并不一致。统一写 `<技能根>/knowledge/...`
    可消除这种歧义。本项即为该约定的回归守卫。
    """
    skill_root = ROOT / SKILL_DIR
    scanned = len(list(skill_root.rglob("*.md"))) if skill_root.is_dir() else 0
    stale = find_skill_tree_bare_paths()

    if not stale:
        return CheckResult(
            "skill_tree_internal_paths",
            "pass",
            f"技能树内路径引用均带 `<技能根>/` 前缀（已扫描 {scanned} 个文档）",
        )

    preview = "；".join(stale[:3])
    more = f"（另有 {len(stale) - 3} 处）" if len(stale) > 3 else ""
    return CheckResult(
        "skill_tree_internal_paths",
        "fail",
        f"技能树内存在 {len(stale)} 处未带 `<技能根>/` 前缀的路径引用：{preview}{more}",
        stale,
    )


# ---------- 汇总与渲染 ----------

def build_results() -> list[CheckResult]:
    """执行所有检查，返回结果列表。"""
    results: list[CheckResult] = []
    results.append(check_version_alignment())
    results.append(check_changelog_exists())
    results.append(check_docs_skill_tree_paths())
    results.append(check_docs_markdown_links())
    results.append(check_skill_tree_internal_paths())
    results.append(check_npm_files_payload())
    results.extend(check_capability_coverage())
    results.extend(check_host_table_consistency())
    results.extend(check_npm_entrypoint())
    results.extend(check_runtime_files_exist())
    results.extend(check_excludes_consistency())
    return results


def render_markdown(results: list[CheckResult]) -> str:
    """渲染 markdown 表格报告。"""
    lines = [
        "# 文档一致性审计报告 (doc_consistency_audit)",
        "",
        f"- 仓库根目录：`{ROOT}`",
        f"- 报告时间：由 doc_consistency_audit.py 实时生成",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for r in results:
        detail = r.detail.replace("|", "\\|")
        lines.append(f"| {r.name} | {r.status} | {detail} |")

    passed = sum(1 for r in results if r.status == "pass")
    warned = sum(1 for r in results if r.status == "warn")
    failed = sum(1 for r in results if r.status == "fail")

    lines.extend(
        [
            "",
            f"- Passed: {passed}",
            f"- Warned: {warned}",
            f"- Failed: {failed}",
            "",
            "## 失败项需修复",
        ]
    )
    for r in results:
        if r.status == "fail":
            lines.append(f"- **{r.name}**: {r.detail}")
    if failed == 0:
        lines.append("- （无）")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit testcase-generator documentation consistency.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式（默认 markdown）",
    )
    args = parser.parse_args()

    results = build_results()
    failed = any(r.status == "fail" for r in results)

    if args.format == "json":
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    else:
        print(render_markdown(results))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
