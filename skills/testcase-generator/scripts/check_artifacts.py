#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_artifacts.py — testcase-generator 用例产物级验收门禁。

`check_consistency.py` 校验的是「技能文档自身是否自洽」；本脚本校验的是
「本技能实际产出的用例集是否落地了清单里的要求」。两者互补，不可互相替代。

针对 v2.3.1 能力评测暴露的三类短板（均为实际发生过的缺陷类型）：
  1. ID 与统计：区分「用例定义」与「索引/追溯引用」，给出唯一用例数，
     防止把索引表里的 ID 重复计入用例规模（EVAL-02/11 的双计问题）
  2. 落地完整性：每条用例是否具备「预期结果 / 前置 / 数据 / 步骤 / 后置」；
     安全类用例是否带 CWE 编号（清单 G2-3-3 有要求，13 份产物 0 落地）
  3. 诚实性：显式标注「不可执行 / 流程项 / 非代码用例」的条目，不得给出
     PASS/FAIL 判定而跳过 SKIP/TBD —— EVAL-12 的 TC-REG-CFG-004 正是此类，
     实测回放时才发现「把测不了当成不合格」

用法：
    python scripts/check_artifacts.py --input <文件或目录> [<文件或目录> ...]
    python scripts/check_artifacts.py --input results/ --strict
    python scripts/check_artifacts.py --input results/ --write-baseline base.json
    python scripts/check_artifacts.py --input results/ --strict --baseline base.json
    python scripts/check_artifacts.py --self-test
    python scripts/check_artifacts.py --input results/ --json

退出码：0 = 通过；1 = 存在 Error（--strict）或较基线退化；2 = 自检失败

── 语义盲区（必须声明，不得把本脚本的输出当作质量结论）──────────────
  1. 只识别 `TC-<...>` 前缀、且以 Markdown 标题或表格首列为载体的用例。
     自由文本描述的用例、其它 ID 体系、图片/附件里的用例，一律不在视野内。
  2. 字段完备性靠关键词匹配，只能回答「有没有写这一栏」，不能回答
     「写的是否具体、是否二元可判定」。「输入数据：按需求填写」同样会过。
  3. 诚实性规则只能抓到**显式标注**的不可执行项；标注为「结构验证」
     却实际需要读 DDL 的隐性不可执行项（如 TC-REG-IDEM-005）抓不到。
     这是所有文本规则的结构性盲区：能看见「写错的话」，看不见「没写的话」。
  4. CWE 只检查有无 `CWE-<数字>`，不校验编号与缺陷类型是否匹配。
  5. 不判断预期结果是否正确、不判断覆盖是否充分、不判断用例能否真的跑起来。
     本脚本是「防复发门禁」，不是评分器。
─────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 规则常量
# ---------------------------------------------------------------------------

CASE_ID_RE = re.compile(r"\bTC-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b")
HEADING_DEF_RE = re.compile(r"^(#{2,6})\s+(TC-[A-Za-z0-9-]+)\b")
# 第三种载体：`**TC-XXX-NNN｜标题**`（EVAL-07 / EVAL-09 采用）
BOLD_DEF_RE = re.compile(r"^\*\*(TC-[A-Za-z0-9-]+)\s*[｜|]")
TABLE_ROW_RE = re.compile(r"^\|\s*(TC-[A-Za-z0-9-]+)\s*\|")
SEPARATOR_ROW_RE = re.compile(r"^\|[\s:\-\|]+\|\s*$")
CWE_RE = re.compile(r"\bCWE-\d+\b", re.I)

# 表头含这些词之一时，该表格被视为「用例明细表」而非「索引/追溯表」
DETAIL_HEADER_WORDS = (
    "场景", "前置", "输入", "测试数据", "步骤", "预期", "期望", "判定",
    "后置", "优先级", "用例描述", "测试点", "操作", "Precondition",
    "Expected", "Steps", "Priority",
)

# 各必填栏的关键词（对标题型用例按块文本匹配；对表格型优先按表头匹配）
FIELD_WORDS: dict[str, tuple[str, ...]] = {
    "expected": ("预期", "期望", "断言", "Expected", "预期结果", "PASS/FAIL"),
    "precond": ("前置", "Precondition", "Given", "准备", "前置条件"),
    "data": ("测试数据", "输入", "Input", "参数", "数据准备",
             "完整请求", "请求", "报文", "payload"),
    "steps": ("步骤", "操作", "Steps", "执行步骤"),
    "postcond": ("后置", "终态", "Postcondition", "状态验证", "后置状态"),
}

# 高置信安全类关键词：命中即要求 CWE 编号（条件触发，避免一刀切）
SECURITY_WORDS = re.compile(
    r"注入|XSS|CSRF|SSRF|越权|路径穿越|目录遍历|硬编码|明文口令|鉴权绕过|"
    r"反序列化|重放|提权|权限提升|密钥泄漏|密钥泄露|脱敏绕过|会话固定",
    re.I,
)

# 显式「不可执行」标注
UNEXEC_WORDS = re.compile(
    r"不可执行|无法执行|不能执行|流程项|非代码用例|静态检查（不可执行）|"
    r"需读取 ?DDL|本机无法|需真实环境|设计评审确认",
    re.I,
)
VERDICT_RE = re.compile(r"\b(PASS|FAIL)\b")
HONEST_RE = re.compile(r"\b(SKIP|TBD|N/A)\b|待定|不适用|未执行|降级|待确认", re.I)

DEFAULT_EXCLUDE = re.compile(
    r"execution-report|能力评测任务集|README|MEMORY|CHANGELOG|baseline\.json", re.I
)

# 后置状态验证可以写在「预期结果」里，不必单列一栏（ISO 29119-3 允许）
STATE_VERIFY_RE = re.compile(
    r"状态|流水|记录|数据库|落库|写入|不变|新增|计数|库存|"
    r"\bDB\b|Redis|\bstatus\b|order\.|查[订流]|读[ `]*Redis", re.I
)
EXPECT_WORDS = ("预期", "期望", "Expected", "断言")


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

class Finding:
    __slots__ = ("level", "check", "location", "message")

    def __init__(self, level: str, check: str, location: str, message: str) -> None:
        self.level = level          # ERROR / WARN / INFO
        self.check = check          # ids / fields / cwe / unexec / stats
        self.location = location
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "check": self.check,
                "location": self.location, "message": self.message}


@dataclass
class Case:
    case_id: str
    kind: str                      # heading / table
    file: str
    lineno: int
    text: str = ""                 # 判定所依据的文本（块或行）
    header: str = ""               # 表格表头（表格型专用）
    columns: int = 0


@dataclass
class Parsed:
    path: Path
    definitions: list[Case] = field(default_factory=list)
    references: list[tuple[str, int]] = field(default_factory=list)
    occurrences: int = 0


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_file(path: Path) -> Parsed:
    """解析单个 Markdown 产物，区分用例定义与索引/追溯引用。

    支持三种用例载体：标题型、加粗行型、明细表格首列型。
    """
    parsed = Parsed(path=path)
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    blocks: list[tuple[int, int, str, str]] = []   # (起始行, 结束行, ID, 载体)
    for i, line in enumerate(lines):
        hm = HEADING_DEF_RE.match(line)
        bm = BOLD_DEF_RE.match(line)
        if hm:
            cid, kind, level = hm.group(2), "heading", len(hm.group(1))
        elif bm:
            cid, kind, level = bm.group(1), "bold", 0
        else:
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            h = re.match(r"^(#{1,6})\s", lines[j])
            if h and (kind != "heading" or len(h.group(1)) <= level):
                end = j
                break
            if kind == "bold" and (BOLD_DEF_RE.match(lines[j])
                                   or lines[j].strip() == "---"):
                end = j
                break
        blocks.append((i, end, cid, kind))

    block_ids = {cid for _, _, cid, _ in blocks}
    for i, end, cid, kind in blocks:
        parsed.definitions.append(Case(
            case_id=cid, kind=kind, file=path.name, lineno=i + 1,
            text="\n".join(lines[i:end]),
        ))

    # 表格：跟踪最近一次表头（含分隔符行）
    header = ""
    header_cols = 0
    pending_header = ""
    for i, line in enumerate(lines):
        if line.lstrip().startswith("|"):
            cells = _cells(line)
            if SEPARATOR_ROW_RE.match(line) and pending_header:
                header = pending_header
                header_cols = len(cells)
                continue
            if not SEPARATOR_ROW_RE.match(line):
                pending_header = line
            m = TABLE_ROW_RE.match(line)
            if not m:
                continue
            cid = m.group(1)
            is_detail = (
                len(cells) >= 6
                and any(w.lower() in header.lower() for w in DETAIL_HEADER_WORDS)
            )
            # 已有块型定义 → 该表格行一定是索引/追溯，不算第二次定义
            if is_detail and cid not in block_ids:
                parsed.definitions.append(Case(
                    case_id=cid, kind="table", file=path.name, lineno=i + 1,
                    text=line, header=header, columns=len(cells),
                ))
            else:
                parsed.references.append((cid, i + 1))
        else:
            if line.strip() == "":
                continue
            header = ""
            header_cols = 0
            pending_header = ""

    parsed.occurrences = sum(len(CASE_ID_RE.findall(ln)) for ln in lines)
    return parsed


# ---------------------------------------------------------------------------
# 检查项
# ---------------------------------------------------------------------------

def check_ids(parsed_files: list[Parsed]) -> tuple[list[Finding], set[str], int]:
    """定义唯一性 + 悬空引用统计。返回 (findings, 全部已定义ID, 定义位置数)。"""
    findings: list[Finding] = []
    seen: dict[str, Case] = {}
    for pf in parsed_files:
        for case in pf.definitions:
            if case.case_id in seen:
                first = seen[case.case_id]
                findings.append(Finding(
                    "ERROR", "ids", f"{case.file}:{case.lineno}",
                    f"用例 ID {case.case_id} 被重复定义（首次：{first.file}:{first.lineno}）",
                ))
            else:
                seen[case.case_id] = case

    defined = set(seen)
    dangling: dict[str, int] = {}
    for pf in parsed_files:
        for cid, _ in pf.references:
            if cid not in defined:
                dangling[cid] = dangling.get(cid, 0) + 1
    if dangling:
        sample = "、".join(sorted(dangling)[:5])
        findings.append(Finding(
            "INFO", "ids", "(全局)",
            f"{len(dangling)} 个被引用但无定义的 ID（多为跨文件追溯或举例），样例：{sample}；不计为用例",
        ))
    return findings, defined, sum(len(p.definitions) for p in parsed_files)


def _has_field(case: Case, key: str) -> bool:
    """只判断「有没有这一栏」，不判断内容是否具体（见模块 docstring 盲区 2）。"""
    words = FIELD_WORDS[key]
    header = case.header if case.kind == "table" else ""
    if header:
        if any(w.lower() in header.lower() for w in words):
            return True
        # 后置验证写在「预期结果」栏里也算数，不强制单列
        if key == "postcond" and any(w in header for w in EXPECT_WORDS):
            return bool(STATE_VERIFY_RE.search(case.text))
        return False
    text = case.text
    if any(w.lower() in text.lower() for w in words):
        return True
    if key == "postcond" and any(w in text for w in EXPECT_WORDS):
        return bool(STATE_VERIFY_RE.search(text))
    return False


def check_fields(parsed_files: list[Parsed]) -> list[Finding]:
    """必填栏完备性。缺「预期结果」= ERROR，其余按文件汇总为 WARN。"""
    findings: list[Finding] = []
    labels = {"expected": "预期结果", "precond": "前置条件",
              "data": "测试数据", "steps": "执行步骤", "postcond": "后置状态"}
    for pf in parsed_files:
        if not pf.definitions:
            continue
        missing: dict[str, list[str]] = {k: [] for k in FIELD_WORDS}
        for case in pf.definitions:
            for key in FIELD_WORDS:
                if not _has_field(case, key):
                    missing[key].append(case.case_id)
        for key, ids in missing.items():
            if not ids:
                continue
            level = "ERROR" if key == "expected" else "WARN"
            sample = "、".join(ids[:3])
            findings.append(Finding(
                level, "fields", f"{pf.path.name} (共 {len(pf.definitions)} 条定义)",
                f"缺「{labels[key]}」{len(ids)} 条（{len(ids)*100//max(1,len(pf.definitions))}%），样例：{sample}",
            ))
    return findings


def check_cwe(parsed_files: list[Parsed]) -> list[Finding]:
    """安全类用例的 CWE 标注（条件触发，按文件汇总，不刷屏）。"""
    findings: list[Finding] = []
    for pf in parsed_files:
        hits = [c for c in pf.definitions
                if SECURITY_WORDS.search(c.text) and not CWE_RE.search(c.text)]
        if hits:
            sample = "、".join(c.case_id for c in hits[:3])
            findings.append(Finding(
                "WARN", "cwe", f"{pf.path.name} (共 {len(pf.definitions)} 条定义)",
                f"{len(hits)} 条安全类用例未标注 CWE 编号（G2-3-3 要求），样例：{sample}；"
                "若项目不采用 CWE 体系，可用 --no-cwe 关闭本检查",
            ))
    return findings


def check_unexecutable(parsed_files: list[Parsed]) -> list[Finding]:
    """显式标注不可执行的条目，不得给出 PASS/FAIL 而不标 SKIP/TBD。"""
    findings: list[Finding] = []
    for pf in parsed_files:
        for case in pf.definitions:
            if not UNEXEC_WORDS.search(case.text):
                continue
            if not VERDICT_RE.search(case.text):
                continue
            if HONEST_RE.search(case.text):
                continue
            findings.append(Finding(
                "ERROR", "unexec", f"{case.file}:{case.lineno}",
                f"{case.case_id} 标注为不可执行/流程项，却给出 PASS/FAIL 判定且未标 SKIP/TBD"
                " —— 把「测不了」写成了「不合格」",
            ))
    return findings


def check_empty(parsed_files: list[Parsed]) -> list[Finding]:
    return [
        Finding("INFO", "stats", pf.path.name,
                "未识别到用例定义（可能是刻意降级/拒绝生成，或使用了非 TC- 前缀）")
        for pf in parsed_files if not pf.definitions
    ]


# ---------------------------------------------------------------------------
# 自检：证明规则既能抓到已知缺陷，也不误伤合法产物
# ---------------------------------------------------------------------------

SELF_TEST_CASES: list[tuple[str, str, str, bool]] = [
    # (名称, Markdown 内容, 期望触发的 check, 是否应触发)
    ("重复定义应被抓",
     "#### TC-X-001 A\n\n| 预期 | 通过 |\n\n#### TC-X-001 B\n\n| 预期 | 通过 |\n",
     "ids", True),
    ("标题明细 + 索引表不应算重复定义",
     "#### TC-X-001 A\n\n前置：x；预期：y\n\n## 索引\n\n| ID | 场景 |\n|---|---|\n| TC-X-001 | A |\n",
     "ids", False),
    ("缺预期结果应被抓",
     "#### TC-X-001 A\n\n前置条件：已登录；步骤：点击按钮\n",
     "fields:expected", True),
    ("流程项 + FAIL 无 SKIP 应被抓",
     "| ID | 场景 | 前置 | 测试数据 | 步骤 | 预期 | 优先级 | 类型 |\n|---|---|---|---|---|---|---|---|\n"
     "| TC-X-001 | 密钥吊销（流程项，非代码用例） | 已泄漏 | 无 | 1) 轮换 | 完成 | P0 | **FAIL** |\n",
     "unexec", True),
    ("流程项 + SKIP 不应被抓",
     "| ID | 场景 | 前置 | 测试数据 | 步骤 | 预期 | 优先级 | 类型 |\n|---|---|---|---|---|---|---|---|\n"
     "| TC-X-001 | 密钥吊销（流程项） | 已泄漏 | 无 | 1) 轮换 | 完成 | P0 | SKIP |\n",
     "unexec", False),
    ("安全类无 CWE 应被抓",
     "| ID | 场景 | 前置 | 测试数据 | 步骤 | 预期 | 优先级 |\n|---|---|---|---|---|---|---|\n"
     "| TC-X-001 | SQL注入绕过 | 无 | ' OR 1=1 | 1) 提交 | 400 | P0 |\n",
     "cwe", True),
    ("安全类带 CWE 不应被抓",
     "| ID | 场景 | 前置 | 测试数据 | 步骤 | 预期 | 优先级 |\n|---|---|---|---|---|---|---|\n"
     "| TC-X-001 | SQL注入绕过（CWE-89） | 无 | ' OR 1=1 | 1) 提交 | 400 | P0 |\n",
     "cwe", False),
    ("无用例的降级文档不应报错",
     "# 信息不足\n\n拒绝生成正式用例，仅列出待澄清问题。\n",
     "ids", False),
]


def run_self_test() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        for name, content, expect, should in SELF_TEST_CASES:
            p = Path(td) / "case.md"
            p.write_text(content, encoding="utf-8")
            pf = parse_file(p)
            fs = (check_ids([pf])[0] + check_fields([pf]) + check_cwe([pf])
                  + check_unexecutable([pf]))
            check_name = expect.split(":")[0]
            if check_name == "fields":
                matched = [f for f in fs if f.check == "fields"
                           and "预期结果" in f.message and f.level == "ERROR"]
            else:
                matched = [f for f in fs if f.check == check_name
                           and f.level in ("ERROR", "WARN")]
            hit = bool(matched)
            status = "OK" if hit == should else "FAIL"
            if hit != should:
                ok = False
            print(f"  [{status:4}] {name}  (期望触发={should}, 实际={hit})")
            for f in fs:
                if f.level in ("ERROR", "WARN"):
                    print(f"         └ {f.level} {f.check}: {f.message[:90]}")

        # 载体覆盖 + 后置放宽：加粗行必须被识别，且「预期里写了状态校验」不报缺后置
        p = Path(td) / "carrier.md"
        p.write_text(
            "**TC-X-001｜用例 A**\n- 前置条件：x\n- 测试数据：amount=1\n"
            "- 执行步骤：1) 提交\n- 预期结果：status=PAID；DB 流水 1 条\n\n---\n\n"
            "**TC-X-002｜用例 B**\n- 预期结果：HTTP 400；status 不变\n",
            encoding="utf-8")
        pf = parse_file(p)
        fs = check_fields([pf])
        carrier_ok = (len(pf.definitions) == 2
                      and all(c.kind == "bold" for c in pf.definitions)
                      and not any("后置状态" in f.message for f in fs))
        if not carrier_ok:
            ok = False
        print(f"  [{'OK' if carrier_ok else 'FAIL':4}] 加粗行载体识别 + 预期内后置验证不误报"
              f"  (定义数={len(pf.definitions)}, "
              f"缺后置告警={sum('后置状态' in f.message for f in fs)})")

    print(f"\n自检结论: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


# ---------------------------------------------------------------------------
# 收集与输出
# ---------------------------------------------------------------------------

def collect_files(inputs: list[str], exclude: re.Pattern[str] | None) -> list[Path]:
    out: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_file():
            candidates = [p]
        elif p.is_dir():
            candidates = sorted(p.glob("*.md"))
        else:
            print(f"[WARN ] 输入不存在，已跳过：{raw}", file=sys.stderr)
            continue
        for c in candidates:
            if exclude and exclude.search(c.name):
                continue
            if c not in out:
                out.append(c)
    return out


def print_report(findings: list[Finding], parsed: list[Parsed],
                 unique: int, def_count: int, naive: int,
                 ratchet: dict[str, Any] | None) -> None:
    print("=" * 68)
    print("testcase-generator 用例产物验收门禁")
    print("=" * 68)
    print(f"扫描文件: {len(parsed)}  |  用例定义位置: {def_count}  |  唯一用例: {unique}")
    print(f"朴素 ID 出现次数: {naive}  |  索引/追溯带来的虚增: {naive - def_count}")
    print("-" * 68)
    for pf in parsed:
        print(f"  {pf.path.name:<34} 定义 {len(pf.definitions):>4}  引用 {len(pf.references):>4}  ID出现 {pf.occurrences:>5}")
    print("-" * 68)
    for f in findings:
        print(f"[{f.level:<5}] {f.check:<7} {f.location:<38} {f.message}")
    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = sum(1 for f in findings if f.level == "WARN")
    print("-" * 68)
    if ratchet:
        print(f"基线锁定：ERROR ≤ {ratchet['errors']} / WARN ≤ {ratchet['warns']} / 唯一用例 ≥ {ratchet['unique_cases']}")
    print(f"ERROR {errors}  |  WARN {warns}")
    print("=" * 68)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="testcase-generator 用例产物验收门禁")
    ap.add_argument("--input", nargs="+", default=["."], help="Markdown 文件或目录（可多个）")
    ap.add_argument("--strict", action="store_true", help="有 Error 时以非零码退出")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--exclude", default=None, help="额外的文件名排除正则")
    ap.add_argument("--no-exclude", action="store_true", help="不做默认排除")
    ap.add_argument("--no-cwe", action="store_true", help="关闭 CWE 检查")
    ap.add_argument("--baseline", default=None, help="基线 JSON：允许存量欠账，但不得退化")
    ap.add_argument("--write-baseline", default=None, help="把当前结果写为基线 JSON")
    ap.add_argument("--self-test", action="store_true", help="运行内置规则自检")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    exclude = None if args.no_exclude else (
        re.compile(DEFAULT_EXCLUDE.pattern + "|" + args.exclude, re.I)
        if args.exclude else DEFAULT_EXCLUDE
    )
    files = collect_files(args.input, exclude)
    if not files:
        print("[ERROR] 未找到可扫描的 Markdown 文件", file=sys.stderr)
        return 1
    parsed = [parse_file(p) for p in files]

    id_findings, defined, def_count = check_ids(parsed)
    findings = (id_findings + check_fields(parsed)
                + ([] if args.no_cwe else check_cwe(parsed))
                + check_unexecutable(parsed) + check_empty(parsed))
    naive = sum(p.occurrences for p in parsed)
    unique = len(defined)

    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = sum(1 for f in findings if f.level == "WARN")

    ratchet: dict[str, Any] | None = None
    if args.baseline:
        bp = Path(args.baseline)
        if not bp.exists():
            print(f"[ERROR] 基线文件不存在：{bp}", file=sys.stderr)
            return 1
        ratchet = json.loads(bp.read_text(encoding="utf-8"))

    if args.write_baseline:
        Path(args.write_baseline).write_text(
            json.dumps({"errors": errors, "warns": warns, "unique_cases": unique,
                        "note": "存量欠账锁定；新增 ERROR/WARN 或用例减少即视为退化"},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"基线已写入：{args.write_baseline}")

    if args.json:
        print(json.dumps({
            "files": len(parsed), "definitions": def_count,
            "unique_cases": unique, "naive_id_occurrences": naive,
            "inflation": naive - def_count,
            "errors": errors, "warns": warns,
            "findings": [f.as_dict() for f in findings],
        }, ensure_ascii=False, indent=2))
    else:
        print_report(findings, parsed, unique, def_count, naive, ratchet)

    if ratchet:
        degraded = (errors > ratchet["errors"] or warns > ratchet["warns"]
                    or unique < ratchet["unique_cases"])
        if not args.json:
            print("结论: FAIL（较基线退化：新增欠账或用例减少）" if degraded
                  else "结论: PASS（存量欠账已锁定，未退化）")
        return 1 if degraded else 0
    if args.strict:
        if not args.json:
            print(f"结论: {'FAIL' if errors else 'PASS'}")
        return 1 if errors else 0
    if not args.json:
        print("结论: 检查完成（未启用 --strict，Error 不影响退出码）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
