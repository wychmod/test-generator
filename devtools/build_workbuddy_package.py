#!/usr/bin/env python3
"""构建 WorkBuddy 开放平台技能市场的上架包。

为什么需要**另一个**打包器
==========================

仓库已有两条分发通道（`.skill` / `.zip` 与 npm），它们的边界由
`skill.manifest.json` 的「运行时文件」+「分发排除」和 `package.json` 的 `files`
分别定义。WorkBuddy 市场是**第三条**通道，规则完全不同：

- 解压后第一层必须是技能目录，**目录最多两层**（`{skill}/{dir}/{file}`）；
- `SKILL.md` 的 frontmatter 必须是平台字段（`display_name` / `display_name_en`
  / `description_zh` / `description_en` / `version` / `author` 等），缺一个就解析失败；
- 包里不该出现 `adapters/`、`docs/`、`skill.manifest.json` 这类**只在仓库语境下
  才成立**的东西 —— 市场用户拿到的是一个独立技能，不是本仓库的快照。

因此本脚本不做「过滤 → 打包」，而是**重排 → 改写 → 校验**：

1. 重排：`knowledge/sources/*.md` → `knowledge/*.md`，`knowledge/scripts/*.py`
   与 `scripts/*.py` 合并进 `scripts/`，其余目录原样保留；
2. 改写：注入平台 frontmatter、把包内失效的跨树链接与路径改写为新布局；
3. 校验：层级、字段、体积，并在**临时解压目录**里实跑 `check_consistency.py`、
   `build_index.py`、`search.py`、`check_artifacts.py --self-test` —— 宁可在这里
   失败，也不要拿解析失败去消耗每天 5 次的提审额度。

用法::

    python devtools/build_workbuddy_package.py            # -> dist/workbuddy/
    python devtools/build_workbuddy_package.py --out DIR
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "skills" / "testcase-generator"
DEFAULT_OUT_DIR = ROOT / "dist" / "workbuddy"

# 市场侧的技能标识与仓库侧的目录名**故意不同**：平台要求 name 全局唯一，
# `testcase-generator` 已被占用。仓库内 `skills/testcase-generator/` 保持原样
# （它是 canonical 路径，被 manifest / adapters / 审计脚本共同依赖）。
PACKAGE_NAME = "mbt-testcase-generator"
ARCHIVE_NAME = f"{PACKAGE_NAME}.zip"

# 平台限制：仅 .zip，且不超过 3 MB。
MAX_ARCHIVE_BYTES = 3 * 1024 * 1024
# 解压后第一层是技能目录，故包内路径深度上限为 2。
MAX_DEPTH = 2

# 包内允许出现的顶层目录（其余一律视为漏网，构建直接失败）。
ALLOWED_TOP_DIRS = {
    "config",
    "knowledge",
    "prompts",
    "references",
    "resources",
    "scripts",
    "templates",
}

# 仓库语境专属、不得流入市场包的文件/目录名。
REPO_ONLY_NAMES = {
    "__pycache__",
    "adapters",
    "docs",
    ".harness",
    "devtools",
    "test",
    "test-output",
    "index.json",
}

# 构建期排除的源文件（相对技能根）。
SOURCE_EXCLUDES = {
    "knowledge/index.json",  # 本地索引产物，用户首次构建时自动生成
}

# 目录重排规则：源相对路径 → 包内相对路径。
# 按键名长度倒序匹配，保证 `knowledge/scripts/x.py` 先于 `knowledge/` 命中。
RELOCATIONS = (
    ("knowledge/scripts/", "scripts/"),
    ("knowledge/sources/README.md", "knowledge/sources-guide.md"),
    ("knowledge/sources/", "knowledge/"),
)

# 文本改写（对包内 .md 与 .py 生效，按顺序应用）。
# 顺序敏感：长路径必须先于短路径替换，否则 `knowledge/sources/<slug>.md`
# 会被 `knowledge/sources/` 抢先吃掉一个前缀。
TEXT_REWRITES = (
    ("knowledge/sources/<slug>.md", "knowledge/<slug>.md"),
    ("knowledge/sources/*.md", "knowledge/*.md"),
    ("`<技能根>/knowledge/sources` 使用说明", "`<技能根>/knowledge` 使用说明"),
    ("knowledge/sources/", "knowledge/"),
    ("knowledge/scripts/", "scripts/"),
    ("写入 sources 并重建索引", "写入 knowledge/ 并重建索引"),
)

# `<技能根>` 的指向说明原本锚定仓库路径（`skills/testcase-generator/`）与某个
# 具体宿主的安装位置（`.claude/skills/...`）。市场包里前者不存在、后者以偏概全，
# 统一改成与宿主无关的表述。
CONVENTION_PATTERNS = (
    (
        re.compile(
            r"> \*\*路径约定\*\*：本文中的 `<技能根>` 指技能目录 "
            r"`skills/testcase-generator/`。激活到宿主后，它就是宿主技能目录"
            r"（如 `\.claude/skills/testcase-generator/`）。"
        ),
        "> **路径约定**：本文中的 `<技能根>` 指本技能目录 —— 解压后即 "
        f"`{PACKAGE_NAME}/`，安装后即宿主分配的技能目录。",
    ),
    (
        re.compile(
            r"> \*\*路径约定\*\*：文中 `<技能根>` 指技能目录 "
            r"`skills/testcase-generator/`，激活到宿主后即宿主技能目录"
            r"（如 `\.claude/skills/testcase-generator/`）。"
        ),
        "> **路径约定**：文中 `<技能根>` 指本技能目录 —— 解压后即 "
        f"`{PACKAGE_NAME}/`，安装后即宿主分配的技能目录。",
    ),
)

# 指向技能树外（仓库 docs/）的 Markdown 链接。市场包里没有 docs/，留着就是死链，
# 且 `check_consistency.py` 的链接检查会直接判 ERROR。降级为行内代码 + 说明。
OUTSIDE_DOC_LINK_RE = re.compile(r"\[`([^`]+)`\]\((?:\.\./)+docs/[^)]*\)")

# `knowledge/sources/README.md` 被提升到 `knowledge/sources-guide.md`，它与
# `llm-ingest-template.md` 从「父目录/子目录」变成了兄弟关系，相对引用要跟着改。
GUIDE_LINK_FIX = (
    "普通用户优先使用 `../llm-ingest-template.md`",
    "普通用户优先使用同目录下的 `llm-ingest-template.md`",
)

# 正文里的仓库语境措辞（manifest 是**仓库**的文件，市场包里不存在，提它只会误导）。
BODY_REWRITES = (
    (
        "本 Skill 对外声明的核心能力（与 `skill.manifest.json` 字段对齐）：",
        "本 Skill 对外声明的核心能力：",
    ),
    (
        "本产物清单对应 `skill.manifest.json` 中声明的全部 7 项核心能力",
        "本产物清单对应本技能声明的全部 7 项核心能力",
    ),
)

# 构建完成后不得再出现的残留标记。
RESIDUAL_TOKENS = (
    "knowledge/sources/",
    "knowledge/scripts/",
    "HOST_COMPATIBILITY.md",
    "skill.manifest.json",
    "DISTRIBUTION.md",
)

# knowledge/README.md 的目录树需要按新布局重画（正则匹配整个围栏块，避免
# 依赖缩进与注释列对齐的具体空格数）。
KB_TREE_RE = re.compile(r"```text\nknowledge/\n.*?\n```", re.S)

KB_TREE_NEW = """```text
knowledge/
├── README.md                    # 用户入口文档（本文）
├── sources-guide.md             # 知识条目写法说明
├── llm-ingest-template.md       # 可直接复制给大模型的录入模板
├── domain-glossary.md           # 示例：术语表
├── project-conventions.md       # 示例：项目规范
├── historical-cases.md          # 示例：历史用例
└── index.json                   # 本地索引产物，不生成、不提交、不分发
```

索引与检索脚本位于 `<技能根>/scripts/`（`build_index.py` / `search.py` / `ingest.py`）。"""


# ---------------------------------------------------------------------------
# 平台 frontmatter
# ---------------------------------------------------------------------------

# 市场展示名。平台要求**同类型资产内唯一**，重名会在上传时被拒。
# 首次提交时「测试用例生成器」已被人占用，故改为突出方法论差异的 MBT 前缀版本。
DISPLAY_NAME = "MBT 测试用例生成器"
DISPLAY_NAME_EN = "MBT Testcase Generator"
AUTHOR = "wychmod"

DESCRIPTION = (
    "从需求文档、PRD、API 规范、源代码、缺陷修复上下文或功能描述中生成结构化、可追溯、"
    "可执行的软件测试用例与测试设计产物。当用户提出生成、扩展、评审、标准化、优化或审计"
    "测试用例、测试场景、测试点清单、MBT 导向测试设计结果或测试文档时使用。"
)
DESCRIPTION_ZH = (
    "六阶段 MBT 测试设计流水线：输入预处理 → 需求抽取 → 代码与契约分析 → 领域建模 → "
    "MBT 设计 → 用例生成，产出需求追溯矩阵与质量门禁报告，可选本地知识库检索，"
    "并随包提供两道可执行的产物校验脚本。"
)
DESCRIPTION_EN = (
    "Six-phase MBT test-design pipeline — input preprocessing, requirement extraction, "
    "code and contract analysis, domain modeling, MBT design, and testcase generation — "
    "delivering a traceability matrix and quality-gate reports, with an optional local "
    "knowledge base and two executable artifact checks."
)
EXAMPLES_ZH = (
    "根据这份 PRD 生成登录模块的测试用例，覆盖边界与异常路径",
    "为订单状态流转做 MBT 导向测试设计，给出覆盖准则与非法路径",
    "评审现有测试用例清单，指出重复、缺失和不可执行的预期结果",
)
EXAMPLES_EN = (
    "Generate login testcases from this PRD, covering boundary and negative paths",
    "Do MBT-oriented test design for the order state machine, with coverage criteria and illegal paths",
    "Review my existing testcase list for duplicates, gaps, and unverifiable expected results",
)


def read_version() -> str:
    """版本号取自 `skill.manifest.json` —— 全仓唯一数据源。"""
    devtools_dir = str(Path(__file__).resolve().parent)
    if devtools_dir not in sys.path:
        sys.path.insert(0, devtools_dir)
    import manifest as manifest_module  # noqa: PLC0415

    return manifest_module.version(manifest_module.load_manifest(use_cache=False))


def yaml_quote(value: str) -> str:
    """JSON 双引号即可当 YAML 双引号标量用；这里避开 `: ` / `#` 之类的裸标量陷阱。"""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_frontmatter(version: str) -> str:
    lines = [
        "---",
        f"name: {PACKAGE_NAME}",
        f"display_name: {yaml_quote(DISPLAY_NAME)}",
        f"display_name_en: {yaml_quote(DISPLAY_NAME_EN)}",
        f"description: {yaml_quote(DESCRIPTION)}",
        f"description_zh: {yaml_quote(DESCRIPTION_ZH)}",
        f"description_en: {yaml_quote(DESCRIPTION_EN)}",
        "examples_zh:",
    ]
    lines += [f"  - {yaml_quote(item)}" for item in EXAMPLES_ZH]
    lines.append("examples_en:")
    lines += [f"  - {yaml_quote(item)}" for item in EXAMPLES_EN]
    lines += [f"version: {version}", f"author: {yaml_quote(AUTHOR)}", "---"]
    return "\n".join(lines)


FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---", re.S)


# ---------------------------------------------------------------------------
# 收集与重排
# ---------------------------------------------------------------------------


def collect_sources() -> list[tuple[Path, str]]:
    """返回 [(源文件绝对路径, 包内相对路径)]。"""
    collected: list[tuple[Path, str]] = []
    for path in sorted(SOURCE_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(SOURCE_DIR).as_posix()
        if any(part in REPO_ONLY_NAMES for part in rel.split("/")):
            continue
        if rel in SOURCE_EXCLUDES:
            continue
        if rel.endswith((".pyc", ".pyo")):
            continue
        # 与 `.skill` 通道的既有约定一致：knowledge/ 下 `_` 开头的模板/草稿不入包
        # （`<技能根>/knowledge/llm-ingest-template.md` 才是对外的录入入口）。
        if rel.startswith("knowledge/") and path.name.startswith("_"):
            continue
        collected.append((path, relocate(rel)))
    return collected


def relocate(rel: str) -> str:
    for source_prefix, target_prefix in RELOCATIONS:
        if rel.startswith(source_prefix):
            return target_prefix + rel[len(source_prefix) :]
    return rel


def dedupe(members: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    """重排可能造成目标路径撞车（如两个 README 落到同一处），必须显式处理。"""
    seen: dict[str, Path] = {}
    for path, target in members:
        if target in seen:
            raise SystemExit(
                f"重排冲突：{seen[target].relative_to(ROOT)} 与 "
                f"{path.relative_to(ROOT)} 都会落到 {target}"
            )
        seen[target] = path
    return members


# ---------------------------------------------------------------------------
# 文本改写
# ---------------------------------------------------------------------------


def rewrite_paths(text: str) -> str:
    for old, new in TEXT_REWRITES:
        text = text.replace(old, new)
    return text


def rewrite_conventions(text: str) -> str:
    for pattern, replacement in CONVENTION_PATTERNS:
        text = pattern.sub(lambda _m: replacement, text)
    return text


def demote_outside_links(text: str) -> str:
    return OUTSIDE_DOC_LINK_RE.sub(
        lambda m: f"`{m.group(1)}`（项目仓库文档，不在本包内）", text
    )


def apply_body_rewrites(text: str) -> str:
    for old, new in BODY_REWRITES:
        text = text.replace(old, new)
    return text


def build_sources_guide(raw: str) -> str:
    """`knowledge/sources/README.md` → `knowledge/sources-guide.md`。"""
    if GUIDE_LINK_FIX[0] not in raw:
        raise SystemExit("sources/README.md 中找不到 `../llm-ingest-template.md` 引用")
    return raw.replace(GUIDE_LINK_FIX[0], GUIDE_LINK_FIX[1])


def build_skill_md(raw: str, version: str) -> str:
    """入口文件：换掉仓库语境 frontmatter，正文沿用通用改写。"""
    if not FRONTMATTER_RE.match(raw):
        raise SystemExit("SKILL.md 缺少 YAML frontmatter，无法注入平台字段")
    body = FRONTMATTER_RE.sub("", raw).lstrip("\r\n")
    return f"{render_frontmatter(version)}\n\n{body}"


def build_knowledge_readme(raw: str) -> str:
    matches = KB_TREE_RE.findall(raw)
    if len(matches) != 1:
        raise SystemExit(
            f"knowledge/README.md 的目录树围栏块数量异常（{len(matches)}），"
            "扁平化布局无法自动重画"
        )
    return KB_TREE_RE.sub(lambda _m: KB_TREE_NEW, raw, count=1)


# ---------------------------------------------------------------------------
# 局部源码改写：扁平化后脚本的路径常量必须跟着走
# ---------------------------------------------------------------------------

# (文件名, 原锚点, 新文本) —— 锚点不存在即失败，避免静默漂移。
SOURCE_PATCHES: dict[str, tuple[tuple[str, str], ...]] = {
    "scripts/build_index.py": (
        (
            "KNOWLEDGE_DIR = SCRIPT_DIR.parent\n",
            'SKILL_DIR = SCRIPT_DIR.parent\n'
            '# 扁平布局：知识条目直接位于 knowledge/，脚本位于 scripts/。\n'
            'KNOWLEDGE_DIR = SKILL_DIR / "knowledge"\n',
        ),
        (
            'SOURCES_DIR = KNOWLEDGE_DIR / "sources"',
            "SOURCES_DIR = KNOWLEDGE_DIR  # 扁平布局：条目与文档同层，靠 frontmatter 区分",
        ),
        (
            '    title = fm.get("title") or path.stem',
            '    title = fm.get("title")\n'
            "    if not title:\n"
            "        # 扁平布局下 knowledge/ 同时存放条目与使用说明：只有带 frontmatter\n"
            "        # `title` 的才算可检索条目，README / 录入模板等文档一律跳过。\n"
            "        return None",
        ),
    ),
    "scripts/search.py": (
        (
            "KNOWLEDGE_DIR = SCRIPT_DIR.parent\n",
            'SKILL_DIR = SCRIPT_DIR.parent\nKNOWLEDGE_DIR = SKILL_DIR / "knowledge"\n',
        ),
    ),
    "scripts/ingest.py": (
        (
            "KNOWLEDGE_DIR = SCRIPT_DIR.parent\n",
            'SKILL_DIR = SCRIPT_DIR.parent\nKNOWLEDGE_DIR = SKILL_DIR / "knowledge"\n',
        ),
        (
            'SOURCES_DIR = KNOWLEDGE_DIR / "sources"',
            "SOURCES_DIR = KNOWLEDGE_DIR  # 扁平布局：条目与文档同层",
        ),
        (
            'PROMPT_PATH = Path(KNOWLEDGE_DIR).parent / "prompts" / "knowledge_ingest_prompt.md"',
            'PROMPT_PATH = Path(SKILL_DIR) / "prompts" / "knowledge_ingest_prompt.md"',
        ),
    ),
    # check_consistency.py 无需改写：仓库与市场包里它都位于 `<技能根>/scripts/`，
    # `Path(__file__).parent.parent` 在两种布局下都指向技能根。
}


def apply_source_patches(name: str, text: str) -> str:
    for anchor, replacement in SOURCE_PATCHES.get(name, ()):
        if anchor not in text:
            raise SystemExit(f"{name} 中找不到预期锚点，扁平化改写失效：{anchor[:60]!r}")
        text = text.replace(anchor, replacement, 1)
    return text


# ---------------------------------------------------------------------------
# 渲染 + 校验
# ---------------------------------------------------------------------------


def render_package(staging: Path, version: str) -> list[str]:
    members = dedupe(collect_sources())
    written: list[str] = []

    for path, target in members:
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw = rewrite_paths(raw)
        raw = rewrite_conventions(raw)
        raw = demote_outside_links(raw)
        raw = apply_body_rewrites(raw)

        if target == "SKILL.md":
            text = build_skill_md(raw, version)
        elif target == "knowledge/README.md":
            text = build_knowledge_readme(raw)
        elif target == "knowledge/sources-guide.md":
            text = build_sources_guide(raw)
        elif target.endswith(".md"):
            text = raw
        elif target.endswith(".py"):
            text = apply_source_patches(target, raw)
        else:
            text = raw

        destination = staging / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8", newline="\n")
        written.append(target)

    # LICENSE 随包分发（MIT 再分发要求），但只放在包根，深度 1。
    license_src = ROOT / "LICENSE"
    if license_src.exists():
        shutil.copyfile(license_src, staging / "LICENSE")
        written.append("LICENSE")

    return sorted(written)


def check_layout(members: list[str]) -> list[str]:
    problems: list[str] = []
    if "SKILL.md" not in members:
        problems.append("缺少 SKILL.md")
    for member in members:
        depth = len(member.split("/"))
        if depth > MAX_DEPTH:
            problems.append(f"目录层级超过 {MAX_DEPTH} 层：{member}")
        if depth == 1 and member not in {"SKILL.md", "LICENSE"}:
            problems.append(f"包根出现非法文件（平台只认 SKILL.md）：{member}")
        if depth >= 2:
            top = member.split("/")[0]
            if top not in ALLOWED_TOP_DIRS:
                problems.append(f"未登记的顶层目录 `{top}/`：{member}")
    return problems


def check_frontmatter(staging: Path, version: str) -> list[str]:
    problems: list[str] = []
    text = (staging / "SKILL.md").read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return ["SKILL.md 无 frontmatter"]

    try:
        import yaml  # noqa: PLC0415
    except ImportError:  # pragma: no cover - 环境缺 yaml 时退化为逐行解析
        yaml = None

    if yaml is not None:
        data = yaml.safe_load(match.group(0).strip("-").strip())
    else:
        data = {}
        for line in match.group(0).splitlines()[1:-1]:
            if ":" in line and not line.startswith((" ", "\t", "-")):
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()

    required = (
        "name",
        "display_name",
        "display_name_en",
        "description",
        "description_zh",
        "description_en",
        "version",
        "author",
    )
    for field in required:
        if not data.get(field):
            problems.append(f"frontmatter 缺必填字段：{field}")

    if data.get("name") != PACKAGE_NAME:
        problems.append(f"name 必须是 {PACKAGE_NAME}，实际 {data.get('name')!r}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(data.get("name", ""))):
        problems.append("name 不符合 kebab-case")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(data.get("version", ""))):
        problems.append(f"version 必须是三段式 SemVer，实际 {data.get('version')!r}")
    elif data.get("version") != version:
        problems.append(f"version 与 manifest 不一致：{data.get('version')} != {version}")
    if len(str(data.get("description", ""))) > 1024:
        problems.append("description 超过 1024 字符")

    for field in ("examples_zh", "examples_en"):
        value = data.get(field)
        if not isinstance(value, list) or not value:
            problems.append(f"{field} 应为非空列表")
    return problems


def check_residuals(staging: Path) -> list[str]:
    problems: list[str] = []
    for path in sorted(staging.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in RESIDUAL_TOKENS:
            if token in text:
                problems.append(f"{path.relative_to(staging).as_posix()} 残留仓库语境引用：{token}")
    return problems


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def check_runtime(staging: Path) -> list[str]:
    """在解压副本里实跑随包脚本 —— 布局改写是否真的可用，只有跑一遍才知道。

    跑在**临时副本**上：`build_index.py` 会写出 `knowledge/index.json`，
    直接在 staging 里跑会把这份本地产物带进 zip。
    """
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp) / PACKAGE_NAME
        shutil.copytree(staging, sandbox)

        steps = (
            ("check_consistency.py", [sys.executable, "scripts/check_consistency.py"]),
            (
                "check_artifacts.py --self-test",
                [sys.executable, "scripts/check_artifacts.py", "--self-test"],
            ),
            ("build_index.py", [sys.executable, "scripts/build_index.py", "--rebuild"]),
            ("search.py", [sys.executable, "scripts/search.py", "密码强度", "--top-k", "3"]),
        )
        for label, cmd in steps:
            result = run(cmd, sandbox)
            if result.returncode != 0:
                tail = (result.stdout + result.stderr).strip().splitlines()[-6:]
                problems.append(f"{label} 退出码 {result.returncode}：{' / '.join(tail)}")

        # 检索必须有命中，否则说明扁平化后的索引扫不到条目（等价于知识库静默失效）。
        search = run([sys.executable, "scripts/search.py", "密码强度", "--json"], sandbox)
        if search.returncode == 0 and '"sections"' in search.stdout:
            if not re.search(r'"(heading|text)"', search.stdout):
                problems.append("search.py 无命中：扁平化后索引未收录知识条目")
    return problems


def check_no_generated_artifacts(staging: Path) -> list[str]:
    """本地生成物不得入包（与 `.gitignore` 的判定保持一致）。"""
    banned = {"knowledge/index.json", "knowledge/_template-glossary.md"}
    return [
        f"本地生成物/模板不应入包：{member}"
        for member in (p.relative_to(staging).as_posix() for p in staging.rglob("*") if p.is_file())
        if member in banned or "__pycache__" in member or member.endswith(".pyc")
    ]


def build_archive(staging: Path, archive_path: Path) -> list[str]:
    members = sorted(p.relative_to(staging).as_posix() for p in staging.rglob("*") if p.is_file())
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for member in members:
            zf.write(staging / member, f"{PACKAGE_NAME}/{member}")
    return members


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 WorkBuddy 市场版技能包")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="输出目录")
    parser.add_argument(
        "--keep-staging",
        action="store_true",
        help="保留解压后的暂存目录，便于人工检查",
    )
    args = parser.parse_args(argv)

    version = read_version()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / ARCHIVE_NAME

    staging_parent = out_dir / "_staging"
    if staging_parent.exists():
        shutil.rmtree(staging_parent)
    staging = staging_parent / PACKAGE_NAME
    staging.mkdir(parents=True)

    print(f"[build] 版本 {version} ← skill.manifest.json")
    members = render_package(staging, version)
    print(f"[build] 渲染 {len(members)} 个文件")

    problems: list[str] = []
    problems += check_layout(members)
    problems += check_frontmatter(staging, version)
    problems += check_no_generated_artifacts(staging)
    problems += check_residuals(staging)
    problems += check_runtime(staging)

    if problems:
        print("\n[FAIL] 上架包校验未通过：")
        for problem in problems:
            print(f"  - {problem}")
        if not args.keep_staging:
            shutil.rmtree(staging_parent)
        return 1

    members = build_archive(staging, archive_path)
    size = archive_path.stat().st_size
    if size > MAX_ARCHIVE_BYTES:
        print(f"[FAIL] 包体积 {size / 1024 / 1024:.2f} MB 超过 3 MB 上限")
        return 1

    print(f"[ok] {archive_path}  ({size / 1024:.1f} KB，{len(members)} 个文件)")
    print(f"     顶层：{', '.join(sorted({m.split('/')[0] for m in members}))}")
    print("     校验：目录层级 / frontmatter / 仓库残留 / 包内脚本实跑 全部通过")
    if args.keep_staging:
        print(f"     暂存目录保留在 {staging}")
    else:
        shutil.rmtree(staging_parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
