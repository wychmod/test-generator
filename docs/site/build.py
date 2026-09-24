#!/usr/bin/env python3
"""项目展示网站构建器（GitHub Pages，main 分支 /docs 目录发布）。

从仓库真实内容生成静态站点：
- 版本 / 核心能力 / 宿主清单 ← skill.manifest.json
- Agent 划分契约 + 运行时阶段提示词 ← docs/architecture/agent-division/ 与 skills/.../prompts/
- 产物输出到 docs/（index.html / agents.html / assets/site/），docs/** 已在分发排除内

用法：python docs/site/build.py
"""
from __future__ import annotations

import base64
import html
import json
import re
import shutil
import sys
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "docs" / "site"
OUT_DIR = ROOT / "docs"
ASSET_OUT = OUT_DIR / "assets" / "site"
GITHUB_BLOB = "https://github.com/wychmod/test-generator/blob/main/"

# ---------------------------------------------------------------- 文档登记

CATEGORIES = [
    ("overview", "划分总览", "为什么提示词天然 agent-ready"),
    ("orchestration", "编排与评审", "谁先跑、失败回退到哪、谁来当裁判"),
    ("agents", "阶段 Agent 契约", "P0 → P5 · 六问契约：身份/输入/执行/输出/门禁/降级"),
    ("prompts", "运行时阶段提示词", "技能树 prompts/ 完整原文"),
    ("contracts", "产物契约字典", "30 项产物命名硬契约与 ID 命名空间"),
]

_AGENT_DIV = "docs/architecture/agent-division"
_PROMPTS = "skills/testcase-generator/prompts"

DOCS = [
    # (id, 标题, 副标题, 分类, 源文件)
    ("division-readme", "Agent 划分总览", "同构结构映射 · Agent 拓扑 · 路径选择", "overview",
     f"{_AGENT_DIV}/README.md"),
    ("orchestration", "编排者 Orchestrator", "输入路由 / 门禁判定 / 回退与降级", "orchestration",
     f"{_AGENT_DIV}/orchestration.md"),
    ("review-agent", "独立评审 Agent", "裁判席三原则 · verdict 协议 · 最低交付", "orchestration",
     f"{_AGENT_DIV}/review-agent.md"),
    ("agent-p0", "P0 · 输入预处理", "唯一必经阶段 · 智能输入处理器", "agents",
     f"{_AGENT_DIV}/agents/p0-input-preprocessing.md"),
    ("agent-p1", "P1 · 需求分析", "可测试需求抽取 · 冲突检测", "agents",
     f"{_AGENT_DIV}/agents/p1-requirements.md"),
    ("agent-p2", "P2 · 代码分析", "可跳过旁路 · 契约推导与缺陷雷达", "agents",
     f"{_AGENT_DIV}/agents/p2-code-analysis.md"),
    ("agent-p3", "P3 · 领域建模", "领域模型 · 状态机 · 参数空间", "agents",
     f"{_AGENT_DIV}/agents/p3-domain-modeling.md"),
    ("agent-p4", "P4 · MBT 设计", "覆盖准则 · 风险导向 · 路径集", "agents",
     f"{_AGENT_DIV}/agents/p4-mbt-design.md"),
    ("agent-p5", "P5 · 用例生成", "结构化用例 · 追溯矩阵 · 90 分门禁", "agents",
     f"{_AGENT_DIV}/agents/p5-testcase-generation.md"),
    ("product-contracts", "产物契约字典", "产物名硬契约 · 被谁消费", "contracts",
     f"{_AGENT_DIV}/product-contracts.md"),
    ("prompt-p0", "Phase 0 · 输入预处理提示词", "输入质量预处理", "prompts",
     f"{_PROMPTS}/phase0_input_preprocessing_prompt.md"),
    ("prompt-p1", "Phase 1 · 需求分析提示词", "可测试需求抽取", "prompts",
     f"{_PROMPTS}/phase1_requirements_prompt.md"),
    ("prompt-p2", "Phase 2 · 代码分析提示词", "代码与接口契约辅助分析", "prompts",
     f"{_PROMPTS}/phase2_code_analysis_prompt.md"),
    ("prompt-p3", "Phase 3 · 领域分析提示词", "领域模型与状态模型构建", "prompts",
     f"{_PROMPTS}/phase3_domain_analysis_prompt.md"),
    ("prompt-p4", "Phase 4 · MBT 设计提示词", "MBT 导向测试设计", "prompts",
     f"{_PROMPTS}/phase4_mbt_design_prompt.md"),
    ("prompt-p5", "Phase 5 · 用例生成提示词", "结构化测试用例生成", "prompts",
     f"{_PROMPTS}/phase5_testcase_generation_prompt.md"),
    ("prompt-kb", "知识入库提示词", "知识库录入与检索", "prompts",
     f"{_PROMPTS}/knowledge_ingest_prompt.md"),
]

# 宿主显示名（键与 lib/activation.js ENVIRONMENTS 对齐；适配方式见 README 多宿主表）
HOST_META = {
    "claude": ("Claude Code", "完整适配"), "codex": ("Codex", "完整适配"),
    "qoder": ("Qoder", "完整适配"), "codebuddy": ("CodeBuddy", "完整适配"),
    "opencode": ("OpenCode", "完整适配"), "commandcode": ("Command Code", "完整适配"),
    "trae": ("Trae", "完整适配"), "cline": ("Cline", "完整适配"),
    "roo": ("Roo Code", "完整适配"), "kilocode": ("Kilo Code", "完整适配"),
    "gemini": ("Gemini CLI", "完整适配"), "qwen": ("Qwen Code", "完整适配"),
    "kiro": ("Kiro", "完整适配"), "droid": ("Factory Droid", "完整适配"),
    "goose": ("Goose", "完整适配"), "openhands": ("OpenHands", "完整适配"),
    "githubcopilot": ("GitHub Copilot", "完整适配"), "amp": ("Amp", "完整适配"),
    "antigravity": ("Google Antigravity", "完整适配"), "pi": ("Pi", "完整适配"),
    "mcpjam": ("MCPJam", "完整适配"), "zencoder": ("Zencoder", "完整适配"),
    "openclaw": ("OpenClaw", "兼容适配"), "clawdbot": ("Clawdbot", "兼容适配"),
    "cursor": ("Cursor", "软适配"), "windsurf": ("Windsurf", "软适配"),
}

# ---------------------------------------------------------------- Markdown 渲染

_md = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists"])
_LINK_RE = re.compile(r'href="([^"]+)"')


def _rewrite_links(rendered: str, src: Path) -> str:
    """把 Markdown 里的相对链接改写为 GitHub blob URL（Pages 只 serve docs/，相对链接会 404）。"""

    def repl(m: re.Match) -> str:
        url = m.group(1)
        if url.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        path_part, _, anchor = url.partition("#")
        target = (src.parent / path_part).resolve()
        try:
            rel = target.relative_to(ROOT)
        except ValueError:
            return m.group(0)
        blob = GITHUB_BLOB + rel.as_posix()
        if anchor:
            blob += "#" + anchor
        return f'href="{blob}"'

    return _LINK_RE.sub(repl, rendered)


def render_doc(src_rel: str) -> tuple[str, str]:
    """返回 (渲染后 HTML, 原始 Markdown)。文件缺失时抛错，拒绝产出占位内容。"""
    src = ROOT / src_rel
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在：{src_rel}")
    raw = src.read_text(encoding="utf-8")
    return _rewrite_links(_md(raw), src), raw


# ---------------------------------------------------------------- 数据生成

def load_manifest() -> dict:
    return json.loads((ROOT / "skill.manifest.json").read_text(encoding="utf-8"))


def core_cap_cards(manifest: dict) -> str:
    caps = manifest["核心能力"]["zh-CN"]
    descs = [
        "对需求 / PRD / API / 源代码等输入先做规范化、缺口识别与质量评分。",
        "从原始输入中提取结构化需求、约束与关键业务规则。",
        "在提供代码或 API 时补充控制流、数据流、异常路径与契约风险。",
        "在存在状态流转或复杂业务规则时建立领域模型与状态机。",
        "围绕覆盖准则、风险导向与状态转换路径做模型化测试设计。",
        "产出可追溯、可执行、可验证的测试用例与场景清单。",
        "在需求 ↔ 用例之间建立双向追溯，并按质量门禁校验产物。",
    ]
    cards = []
    for i, (cap, desc) in enumerate(zip(caps, descs), 1):
        cards.append(
            f'<div class="cap-card reveal"><span class="cap-num">{i:02d}</span>'
            f'<h3>{html.escape(cap)}</h3><p>{html.escape(desc)}</p></div>'
        )
    return "\n".join(cards)


def host_chips(manifest: dict) -> str:
    keys = list(manifest["宿主适配入口"].keys())
    chips = []
    for k in keys:
        name, kind = HOST_META.get(k, (k, "完整适配"))
        cls = {"完整适配": "full", "兼容适配": "compat", "软适配": "soft"}[kind]
        chips.append(
            f'<span class="host-chip {cls}" title="{kind} · test-generator activate {k}">'
            f'{html.escape(name)}</span>'
        )
    return "\n".join(chips)


# ---------------------------------------------------------------- 模板装配

def fill(template: str, mapping: dict[str, str]) -> str:
    out = template
    for key, val in mapping.items():
        token = "{{" + key + "}}"
        if token not in out:
            raise KeyError(f"模板中未找到占位符 {token}")
        out = out.replace(token, val)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover:
        raise ValueError(f"存在未替换的占位符：{leftover}")
    return out


def build_agents_page(version: str) -> str:
    nav_groups: dict[str, list[str]] = {cid: [] for cid, _, _ in CATEGORIES}
    sections = []
    data_js = []
    for doc_id, title, sub, cat, src in DOCS:
        body, raw = render_doc(src)
        nav_groups[cat].append(
            f'<button class="doc-link" data-doc="{doc_id}" data-title="{html.escape(title.lower())}">'
            f'<span class="doc-link-title">{html.escape(title)}</span>'
            f'<span class="doc-link-sub">{html.escape(sub)}</span></button>'
        )
        b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        sections.append(
            f'<article class="doc-panel" id="doc-{doc_id}" hidden>'
            f'<div class="doc-toolbar"><div><h2 class="doc-title">{html.escape(title)}</h2>'
            f'<p class="doc-sub">{html.escape(sub)} · 源文件 <code>{html.escape(src)}</code></p></div>'
            f'<button class="copy-btn" data-copy-raw="{doc_id}">复制提示词原文</button></div>'
            f'<div class="doc-content">{body}</div></article>'
        )
        data_js.append(f'"{doc_id}":"{b64}"')

    nav_html = []
    for cid, cname, cdesc in CATEGORIES:
        items = "\n".join(nav_groups[cid])
        nav_html.append(
            f'<div class="nav-group"><button class="nav-group-head" data-group="{cid}">'
            f'<span>{html.escape(cname)}</span>'
            f'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg></button>'
            f'<p class="nav-group-desc">{html.escape(cdesc)}</p>'
            f'<div class="nav-group-items" id="group-{cid}">{items}</div></div>'
        )

    tpl = (SITE_DIR / "templates" / "agents.html").read_text(encoding="utf-8")
    return fill(tpl, {
        "VERSION": version,
        "DOC_NAV": "\n".join(nav_html),
        "DOC_SECTIONS": "\n".join(sections),
        "DOC_RAW_DATA": "window.PROMPT_RAW={" + ",".join(data_js) + "};",
    })


def build_index_page(manifest: dict) -> str:
    version = manifest["版本"]
    tpl = (SITE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return fill(tpl, {
        "VERSION": version,
        "HOST_COUNT": str(len(manifest["宿主适配入口"])),
        "CORE_CAP_CARDS": core_cap_cards(manifest),
        "HOST_CHIPS": host_chips(manifest),
    })


def main() -> int:
    manifest = load_manifest()
    ASSET_OUT.mkdir(parents=True, exist_ok=True)
    for asset in (SITE_DIR / "assets").iterdir():
        if asset.is_file():
            shutil.copy2(asset, ASSET_OUT / asset.name)

    (OUT_DIR / "index.html").write_text(build_index_page(manifest), encoding="utf-8")
    (OUT_DIR / "agents.html").write_text(build_agents_page(manifest["版本"]), encoding="utf-8")
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"[build] version={manifest['版本']} docs={len(DOCS)} "
          f"hosts={len(manifest['宿主适配入口'])}")
    print(f"[build] -> {OUT_DIR / 'index.html'}")
    print(f"[build] -> {OUT_DIR / 'agents.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
