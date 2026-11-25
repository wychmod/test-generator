#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_consistency.py — testcase-generator 技能文档自洽性校验。

检查 4 类问题（均为 v2.3.0 实际发生过的缺陷类型）：
  1. 权重守恒：每个 Phase 的组声明权重合计 = 100，且每组「检查项权重和 = 组声明权重」
  2. 检查项 ID：唯一性 + 命名规范（只允许 G<阶段>-<组>-<序号> 三段式）
  3. YAML 代码块：所有 ```yaml 块必须能被解析
  4. 内部链接：Markdown 相对链接目标必须存在

用法：
    python scripts/check_consistency.py
    python scripts/check_consistency.py --strict      # 有 Error 时非零退出
    python scripts/check_consistency.py --json        # 机器可读输出

退出码：0 = 全部通过（或仅 Warning）；1 = 存在 Error（仅 --strict 时）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------
# 数据模型
# ----------------------------------------------------------------------------

class Finding:
    """一条校验发现。"""

    __slots__ = ("level", "check", "location", "message")

    def __init__(self, level: str, check: str, location: str, message: str) -> None:
        self.level = level          # ERROR / WARN / INFO
        self.check = check          # weights / ids / yaml / links
        self.location = location    # 文件:行号
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "check": self.check,
            "location": self.location,
            "message": self.message,
        }


# ----------------------------------------------------------------------------
# 1. 权重守恒
# ----------------------------------------------------------------------------

GROUP_RE = re.compile(r"^###\s+(G(\d)\.(\d))[:：].*?Weight[:：]\s*(\d+)%", re.I)
ITEM_RE = re.compile(r"^\|\s*(G\d-\d-\d+)\s*\|.*?\|\s*(\d+)\s*\|\s*$")


def parse_checklist(path: Path) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    """解析 quality_checklist.md，返回 {组ID: {declared, phase, items}}。"""
    findings: list[Finding] = []
    groups: dict[str, dict[str, Any]] = {}

    text = path.read_text(encoding="utf-8-sig")
    current: str | None = None

    for lineno, line in enumerate(text.splitlines(), 1):
        gm = GROUP_RE.match(line)
        if gm:
            gid = gm.group(1)
            groups[gid] = {
                "declared": int(gm.group(4)),
                "phase": gm.group(2),
                "items": [],
                "line": lineno,
            }
            current = gid
            continue

        im = ITEM_RE.match(line)
        if im and current:
            groups[current]["items"].append(
                {"id": im.group(1), "weight": int(im.group(2)), "line": lineno}
            )

    if not groups:
        findings.append(
            Finding("ERROR", "weights", str(path), "未解析到任何检查组，格式可能已变更")
        )
        return groups, findings

    # 组内守恒
    for gid, g in groups.items():
        actual = sum(i["weight"] for i in g["items"])
        if not g["items"]:
            findings.append(
                Finding("ERROR", "weights", f"{path.name}:{g['line']}",
                        f"{gid} 未解析到检查项")
            )
        elif actual != g["declared"]:
            findings.append(
                Finding(
                    "ERROR", "weights", f"{path.name}:{g['line']}",
                    f"{gid} 组内权重失衡：声明 {g['declared']}，"
                    f"检查项之和 {actual}（差 {actual - g['declared']:+d}）",
                )
            )

    # 未被权重表解析的 G 行：仅在「该表本身带权重列」时才视为异常
    marked = {i["line"] for g in groups.values() for i in g["items"]}
    all_lines = text.splitlines()

    def table_has_weight_column(idx: int) -> bool:
        """向上找到当前表格的表头，判断是否含『权重』列。"""
        j = idx - 1
        while j >= 0 and all_lines[j].lstrip().startswith("|"):
            if re.match(r"^\|[\s:|-]+\|$", all_lines[j].strip()):
                header = all_lines[j - 1] if j > 0 else ""
                return "权重" in header
            j -= 1
        return False

    for lineno, line in enumerate(all_lines, 1):
        if lineno in marked:
            continue
        if re.match(r"^\|\s*G\d", line) and not ITEM_RE.match(line):
            if table_has_weight_column(lineno - 1):
                findings.append(
                    Finding("ERROR", "weights", f"{path.name}:{lineno}",
                            f"该行在带权重列的表中却未被解析（缺少权重值？）："
                            f"{line.strip()[:60]}")
                )
            else:
                findings.append(
                    Finding("INFO", "weights", f"{path.name}:{lineno}",
                            f"非计分检查项（所在表无权重列）已跳过：{line.strip()[:50]}")
                )

    # 阶段合计
    by_phase: dict[str, int] = {}
    for g in groups.values():
        by_phase.setdefault(g["phase"], 0)
        by_phase[g["phase"]] += g["declared"]
    for phase, total in sorted(by_phase.items()):
        if total != 100:
            findings.append(
                Finding("ERROR", "weights", path.name,
                        f"Phase {phase} 组权重合计 {total}，应为 100（差 {total - 100:+d}）")
            )

    # 全局期望值：检查项总数 126，总权重 600（6 阶段 × 100）
    total_items = sum(len(g["items"]) for g in groups.values())
    total_weight = sum(i["weight"] for g in groups.values() for i in g["items"])
    findings.append(
        Finding("INFO", "weights", path.name,
                f"解析结果：{len(groups)} 组 / {total_items} 个检查项 / 权重总和 {total_weight}")
    )
    return groups, findings


# ----------------------------------------------------------------------------
# 2. 检查项 ID
# ----------------------------------------------------------------------------

ID_STRICT_RE = re.compile(r"^G(\d)-(\d)-(\d+)$")
ID_LOOSE_RE = re.compile(r"^G(\d+)-(\d+)$")


def check_ids(groups: dict[str, dict[str, Any]], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, str] = {}

    for gid, g in groups.items():
        phase_from_group = gid[1]           # G1.2 -> 1
        group_no = gid.split(".")[1]        # G1.2 -> 2

        for item in g["items"]:
            iid = item["id"]
            if iid in seen:
                findings.append(
                    Finding("ERROR", "ids", f"{path.name}:{item['line']}",
                            f"检查项 ID 重复：{iid}（首次出现于 {seen[iid]}）")
                )
            seen[iid] = f"{path.name}:{item['line']}"

            m = ID_STRICT_RE.match(iid)
            if not m:
                findings.append(
                    Finding("ERROR", "ids", f"{path.name}:{item['line']}",
                            f"检查项 ID 不符合 G<阶段>-<组>-<序号> 规范：{iid}")
                )
                continue

            if m.group(1) != phase_from_group or m.group(2) != group_no:
                findings.append(
                    Finding("ERROR", "ids", f"{path.name}:{item['line']}",
                            f"{iid} 与所属组 {gid} 的编号不对应"
                            f"（期望 G{phase_from_group}-{group_no}-x）")
                )
    return findings


def check_loose_ids_in_docs(docs: list[Path], checklist: Path) -> list[Finding]:
    """其它文档中不应再出现两段式 Gx-y（与 阶段-组 前缀同形）。"""
    findings: list[Finding] = []
    for doc in docs:
        if doc == checklist:
            continue
        for lineno, line in enumerate(doc.read_text(encoding="utf-8-sig").splitlines(), 1):
            for m in re.finditer(r"`(G\d-\d+)`", line):
                findings.append(
                    Finding("ERROR", "ids", f"{doc.name}:{lineno}",
                            f"引用了两段式 ID `{m.group(1)}`，"
                            f"应改为组号 `G{m.group(1)[1]}.{m.group(1)[3]}` "
                            f"或三段式 `{m.group(1)}-x`")
                )
    return findings


# ----------------------------------------------------------------------------
# 3. YAML 代码块
# ----------------------------------------------------------------------------

def check_yaml_blocks(docs: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        import yaml  # type: ignore
    except ImportError:
        findings.append(
            Finding("WARN", "yaml", "-", "PyYAML 未安装，跳过 YAML 校验（pip install pyyaml）")
        )
        return findings

    for doc in docs:
        lines = doc.read_text(encoding="utf-8-sig").splitlines()
        start: int | None = None
        body: list[str] = []

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped in ("```yaml", "```yml"):
                start, body = lineno, []
                continue
            if start is not None and stripped == "```":
                try:
                    yaml.safe_load("\n".join(body))
                except Exception as exc:  # noqa: BLE001
                    detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
                    findings.append(
                        Finding("ERROR", "yaml", f"{doc.name}:{start}",
                                f"YAML 块无法解析（{type(exc).__name__}: {detail}）")
                    )
                start = None
                continue
            if start is not None:
                body.append(line)
    return findings


# ----------------------------------------------------------------------------
# 4. 内部链接
# ----------------------------------------------------------------------------

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)")


def check_links(docs: list[Path], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for doc in docs:
        for lineno, line in enumerate(doc.read_text(encoding="utf-8-sig").splitlines(), 1):
            for m in LINK_RE.finditer(line):
                target = m.group(1).strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (doc.parent / target).resolve()
                if not resolved.exists():
                    findings.append(
                        Finding("ERROR", "links", f"{doc.name}:{lineno}",
                                f"链接目标不存在：{target}")
                    )
    return findings


# ----------------------------------------------------------------------------
# 5. 章节编号连续性（prompts/*.md 的顶级 ## N. 必须从 1 连续递增）
# ----------------------------------------------------------------------------

TOP_SECTION_RE = re.compile(r"^## (\d+)\.\s")


def check_sections(docs: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for doc in docs:
        if doc.parent.name != "prompts":
            continue
        nums: list[int] = []
        in_fence = False
        for line in doc.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                info = stripped[3:].strip()
                if not in_fence:
                    # 只有带 info 的围栏才开启；裸 ``` 在没有开启围栏时是杂散标记
                    if info:
                        in_fence = True
                else:
                    # 围栏内：裸 ``` 关闭；带 info 的是嵌套块（如 ```markdown 内嵌 ```yaml），保持开启
                    if not info:
                        in_fence = False
                continue
            if in_fence:
                continue
            m = TOP_SECTION_RE.match(line)
            if m:
                nums.append(int(m.group(1)))
        if not nums:
            continue
        missing = [i for i in range(1, max(nums) + 1) if i not in nums]
        dup = sorted({n for n in nums if nums.count(n) > 1})
        if missing:
            findings.append(
                Finding("ERROR", "sections", doc.name,
                        f"顶级章节缺号 {missing}（实际序列 {nums}）")
            )
        if dup:
            findings.append(
                Finding("ERROR", "sections", doc.name, f"顶级章节编号重复 {dup}")
            )
        if nums != sorted(nums):
            findings.append(
                Finding("ERROR", "sections", doc.name, f"顶级章节顺序错乱 {nums}")
            )
    return findings


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def collect_docs(root: Path) -> list[Path]:
    skip_dirs = {"avatars", "__pycache__", "knowledge"}
    docs: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in skip_dirs for part in path.parts):
            continue
        docs.append(path)
    return sorted(docs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="testcase-generator 文档自洽性校验")
    parser.add_argument("--strict", action="store_true", help="有 Error 时以非零码退出")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--root", default=str(ROOT), help="技能根目录")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    checklist = root / "resources" / "quality_checklist.md"
    docs = collect_docs(root)

    findings: list[Finding] = []

    if not checklist.exists():
        findings.append(Finding("ERROR", "weights", str(checklist), "质量清单不存在"))
        groups: dict[str, dict[str, Any]] = {}
    else:
        groups, wf = parse_checklist(checklist)
        findings.extend(wf)
        findings.extend(check_ids(groups, checklist))

    findings.extend(check_loose_ids_in_docs(docs, checklist))
    findings.extend(check_yaml_blocks(docs))
    findings.extend(check_links(docs, root))
    findings.extend(check_sections(docs))

    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    infos = [f for f in findings if f.level == "INFO"]

    if args.json:
        print(json.dumps(
            {
                "summary": {
                    "errors": len(errors),
                    "warnings": len(warns),
                    "infos": len(infos),
                    "files_scanned": len(docs),
                },
                "findings": [f.as_dict() for f in findings],
            },
            ensure_ascii=False,
            indent=2,
        ))
        return 1 if (args.strict and errors) else 0

    print("=" * 68)
    print("testcase-generator 文档自洽性校验")
    print("=" * 68)
    print(f"扫描范围: {root}")
    print(f"文档数量: {len(docs)}  |  检查组: {len(groups)}")
    print("-" * 68)

    for f in infos:
        print(f"[INFO ] {f.check:6} {f.message}")

    if not errors and not warns:
        print("\n全部通过：权重守恒、ID 唯一且规范、YAML 可解析、链接可达。")
    else:
        for f in errors:
            print(f"[ERROR] {f.check:6} {f.location}  {f.message}")
        for f in warns:
            print(f"[WARN ] {f.check:6} {f.location}  {f.message}")

    print("-" * 68)
    print(f"ERROR {len(errors)}  |  WARN {len(warns)}")
    status = "PASS" if not errors else "FAIL"
    print(f"结论: {status}")
    print("=" * 68)

    return 1 if (args.strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main())
