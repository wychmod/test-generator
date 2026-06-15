#!/usr/bin/env python3
"""Incremental code-line scanner for Phase 2 code analysis.

The scanner is intentionally lightweight: it parses a unified diff,
extracts added lines, maps those lines to PRD requirement candidates by
token overlap, and flags obvious bug-risk patterns. It produces structured
context for the Phase 2 prompt; it is not a replacement for full static
analysis.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


HUNK_RE = re.compile(r"@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")
REQ_ID_RE = re.compile(r"(?<![A-Z0-9_])(?:[A-Z][A-Z0-9_]*-)+[A-Z0-9_]*\d+(?![A-Z0-9_])")
ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
CHINESE_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")

REQUIREMENT_HINTS = (
    "must",
    "should",
    "shall",
    "require",
    "requires",
    "required",
    "support",
    "validate",
    "reject",
    "return",
    "cannot",
    "不得",
    "必须",
    "应该",
    "应当",
    "需要",
    "支持",
    "校验",
    "验证",
    "返回",
    "拒绝",
    "禁止",
)

STOPWORDS = {
    "and",
    "or",
    "if",
    "else",
    "elif",
    "for",
    "while",
    "return",
    "true",
    "false",
    "none",
    "null",
    "self",
    "this",
    "def",
    "class",
    "const",
    "let",
    "var",
    "function",
    "async",
    "await",
    "import",
    "from",
}

BUG_RULES = [
    {
        "rule_id": "HARDCODED_SECRET",
        "severity": "critical",
        "category": "security",
        "pattern": re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"][^'\"]{6,}['\"]"
        ),
        "message": "Added line appears to hardcode a credential or secret.",
    },
    {
        "rule_id": "BARE_EXCEPT",
        "severity": "major",
        "category": "reliability",
        "pattern": re.compile(r"^\s*except\s*:\s*(?:#.*)?$"),
        "message": "Bare except can hide unrelated runtime failures.",
    },
    {
        "rule_id": "DYNAMIC_EVAL",
        "severity": "critical",
        "category": "security",
        "pattern": re.compile(r"\b(eval|exec)\s*\("),
        "message": "Dynamic code execution can become code injection.",
    },
    {
        "rule_id": "SQL_STRING_CONCAT",
        "severity": "critical",
        "category": "security",
        "pattern": re.compile(r"(?i)\b(select|insert|update|delete)\b.*(\+|%|\{.*\})"),
        "message": "SQL built by string concatenation can introduce injection risk.",
    },
]


def split_identifier(token: str) -> Iterable[str]:
    for part in token.split("_"):
        for item in re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", part).split():
            lowered = item.lower()
            if lowered and lowered not in STOPWORDS:
                yield lowered


def extract_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in ASCII_TOKEN_RE.findall(text):
        lowered = token.lower()
        if lowered not in STOPWORDS:
            tokens.add(lowered)
        tokens.update(split_identifier(token))
    for token in CHINESE_TOKEN_RE.findall(text):
        tokens.add(token)
    return tokens


def normalize_path(raw: str) -> str:
    if raw.startswith("a/") or raw.startswith("b/"):
        return raw[2:]
    return raw


def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    old_line: Optional[int] = None
    new_line: Optional[int] = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            path = normalize_path(parts[-1]) if len(parts) >= 4 else "unknown"
            current = {
                "path": path,
                "status": "modified",
                "added_lines": [],
                "deleted_lines": [],
                "hunks": [],
            }
            files.append(current)
            old_line = None
            new_line = None
            continue

        if current is None:
            continue

        if raw_line.startswith("new file mode"):
            current["status"] = "added"
            continue
        if raw_line.startswith("deleted file mode"):
            current["status"] = "deleted"
            continue
        if raw_line.startswith("+++ "):
            target = raw_line[4:].strip()
            if target != "/dev/null":
                current["path"] = normalize_path(target)
            continue
        if raw_line.startswith("--- "):
            continue

        hunk_match = HUNK_RE.match(raw_line)
        if hunk_match:
            old_line = int(hunk_match.group("old"))
            new_line = int(hunk_match.group("new"))
            current["hunks"].append(raw_line)
            continue

        if old_line is None or new_line is None:
            continue

        if raw_line.startswith("+"):
            current["added_lines"].append(
                {"new_line": new_line, "content": raw_line[1:]}
            )
            new_line += 1
        elif raw_line.startswith("-"):
            current["deleted_lines"].append(
                {"old_line": old_line, "content": raw_line[1:]}
            )
            old_line += 1
        elif raw_line.startswith(" "):
            old_line += 1
            new_line += 1

    return files


# 代码句式的"动作动词"——行以这些开头时几乎不可能是声明性需求
# (Python/常见命令式语言)。REQ-* / must/should/hint 命中时仍可豁免。
_CODE_VERB_PREFIXES = (
    "return ",
    "if ",
    "for ",
    "while ",
    "def ",
    "class ",
    "raise ",
    "yield ",
    "print(",
    "import ",
    "from ",
    "pass\n",
    "continue",
    "break",
    "self.",
    "this.",
    "const ",
    "let ",
    "var ",
    "function ",
    "=>",
)


TRIPLE_SINGLE = "'" + "''"  # 避开文件级 docstring 的 '"""' 闭合冲突


def _looks_like_python_source(prd_text: str) -> bool:
    # 粗略判断 PRD 文本是否本身就是 Python 源代码（而非 Markdown 需求文档）。
    for raw in prd_text.splitlines()[:5]:
        stripped = raw.lstrip()
        if stripped.startswith(("def ", "class ", "import ", "from ")):
            return True
        if stripped.startswith("#!") and "python" in stripped:
            return True
    return False


def _is_inside_def_docstring(prd_text: str, line_index: int) -> bool:
    # 判断第 line_index 行是否在某个 def 后紧跟的 docstring 区间内。
    # 这是 Python 源码里真正的"干扰项"——函数 docstring 经常被错误识别为需求。
    # 其他位置（比如模块顶层的 BUGFIX_NOTE 这种字符串字面量）
    # 不在此过滤范围内，因为那才是用户写 PRD 文本的地方。
    lines = prd_text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        stripped = lines[i].lstrip()
        if stripped.startswith("def ") and stripped.rstrip().endswith(":"):
            # 找这个 def 后面紧跟的 docstring 区间
            j = i + 1
            # 跳过空行
            while j < n and not lines[j].strip():
                j += 1
            if j < n and lines[j].lstrip().startswith('"""'):
                # 单行 docstring
                if '"""' in lines[j][lines[j].index('"""') + 3:]:
                    if line_index == j:
                        return True
                    i = j + 1
                    continue
                # 多行 docstring
                start = j
                k = j + 1
                while k < n and '"""' not in lines[k]:
                    k += 1
                end = k  # 包含闭合行
                if start <= line_index <= end:
                    return True
                i = end + 1
                continue
        i += 1
    return False


def extract_requirements(prd_text: str) -> List[Dict[str, Any]]:
    """从 PRD 文本中抽取结构化需求，过滤代码块/字符串字面量/代码句式。"""
    requirements: List[Dict[str, Any]] = []
    auto_index = 1

    in_fenced_code = False
    in_indented_code = False
    lines = prd_text.splitlines()
    is_python_source = _looks_like_python_source(prd_text)

    for line_index, raw_line in enumerate(lines):
        # 1) Markdown fenced code block：``` 开头 / 结尾
        stripped = raw_line.lstrip()
        if stripped.startswith("```"):
            in_fenced_code = not in_fenced_code
            continue
        if in_fenced_code:
            continue

        line = raw_line.strip(" \t-*#>")
        if not line:
            in_indented_code = False  # 空行重置缩进代码状态
            continue

        # 2) Markdown indented code block (4+ 空格) 或 tab 开头
        if raw_line.startswith("    ") or raw_line.startswith("\t"):
            in_indented_code = True
            continue
        if in_indented_code:
            # 缩进代码块遇到非空、非缩进行即结束
            in_indented_code = False

        # 3) Python 源码里的函数 docstring 区间（仅当 PRD 文本是 .py 时过滤）
        if is_python_source and _is_inside_def_docstring(prd_text, line_index):
            continue

        lower = line.lower()
        ids = REQ_ID_RE.findall(line)
        has_hint = any(hint in lower for hint in REQUIREMENT_HINTS)
        starts_with_code_verb = line.startswith(_CODE_VERB_PREFIXES) or lower.startswith(
            tuple(_CODE_VERB_PREFIXES)
        )

        # 有显式 REQ-* ID：直接当作需求
        # 否则必须命中 hint 且不是命令式代码句式
        looks_like_requirement = bool(ids) or (has_hint and not starts_with_code_verb)
        if not looks_like_requirement:
            continue

        req_id = ids[0] if ids else f"REQ-AUTO-{auto_index:03d}"
        if not ids:
            auto_index += 1
        requirements.append(
            {
                "id": req_id,
                "text": line,
                "tokens": sorted(extract_tokens(line)),
            }
        )

    return requirements


def match_requirements(tokens: set[str], requirements: List[Dict[str, Any]], *, minimum: int) -> List[str]:
    scored: List[tuple[int, str]] = []
    for requirement in requirements:
        overlap = tokens.intersection(requirement["tokens"])
        if len(overlap) >= minimum:
            scored.append((len(overlap), requirement["id"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[1] for item in scored]


def analyze_prd_alignment(line: str, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
    tokens = extract_tokens(line)
    matched_ids = match_requirements(tokens, requirements, minimum=2)
    if matched_ids:
        return {"status": "matched", "requirement_ids": matched_ids}
    if requirements and line.strip():
        return {"status": "needs_review", "requirement_ids": []}
    return {"status": "unassessed", "requirement_ids": []}


def scan_potential_bugs(files: List[Dict[str, Any]], requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for changed_file in files:
        for added in changed_file["added_lines"]:
            content = added["content"]
            tokens = extract_tokens(content)
            requirement_ids = match_requirements(tokens, requirements, minimum=1)
            for rule in BUG_RULES:
                if rule["pattern"].search(content):
                    findings.append(
                        {
                            "rule_id": rule["rule_id"],
                            "severity": rule["severity"],
                            "category": rule["category"],
                            "file": changed_file["path"],
                            "line": added["new_line"],
                            "code": content,
                            "message": rule["message"],
                            "requirement_ids": requirement_ids,
                        }
                    )
    return findings


def analyze_scan(diff_text: str, prd_text: str = "") -> Dict[str, Any]:
    files = parse_unified_diff(diff_text)
    requirements = extract_requirements(prd_text) if prd_text else []

    for changed_file in files:
        for added in changed_file["added_lines"]:
            added["prd_alignment"] = analyze_prd_alignment(added["content"], requirements)

    potential_bugs = scan_potential_bugs(files, requirements)
    added_lines = sum(len(item["added_lines"]) for item in files)
    deleted_lines = sum(len(item["deleted_lines"]) for item in files)
    needs_review = sum(
        1
        for item in files
        for line in item["added_lines"]
        if line["prd_alignment"]["status"] == "needs_review"
    )

    return {
        "summary": {
            "changed_files": len(files),
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "requirements_loaded": len(requirements),
            "prd_needs_review_lines": needs_review,
            "potential_bugs": len(potential_bugs),
        },
        "requirements": [
            {"id": item["id"], "text": item["text"]} for item in requirements
        ],
        "files": files,
        "potential_bugs": potential_bugs,
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def collect_git_diff(repo: Path, base: str, head: str, cached: bool) -> str:
    cmd = ["git", "diff", "--unified=0", "--no-ext-diff"]
    if cached:
        cmd.append("--cached")
    else:
        cmd.extend([base, head])
    proc = subprocess.run(
        cmd,
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return proc.stdout


def render_markdown(result: Dict[str, Any]) -> str:
    lines = ["# Incremental Code Scan", "", "## Summary", ""]
    for key, value in result["summary"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Added Lines", ""])
    for changed_file in result["files"]:
        lines.append(f"### `{changed_file['path']}`")
        for added in changed_file["added_lines"]:
            alignment = added["prd_alignment"]
            reqs = ", ".join(alignment["requirement_ids"]) or "-"
            lines.append(
                f"- L{added['new_line']} `{added['content'].strip()}` "
                f"=> {alignment['status']} ({reqs})"
            )

    lines.extend(["", "## Potential Bugs", ""])
    if not result["potential_bugs"]:
        lines.append("- None detected by lightweight rules.")
    for bug in result["potential_bugs"]:
        reqs = ", ".join(bug["requirement_ids"]) or "-"
        lines.append(
            f"- {bug['severity']} {bug['rule_id']} at "
            f"`{bug['file']}:{bug['line']}` ({reqs}): {bug['message']}"
        )

    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan incremental code lines and map them to PRD requirements."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="HEAD~1")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--cached", action="store_true", help="scan staged changes")
    parser.add_argument("--diff-file", type=Path, help="read unified diff from file")
    parser.add_argument("--prd", type=Path, help="PRD markdown/text file")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path, help="write output to file")
    args = parser.parse_args(argv)

    diff_text = read_text(args.diff_file) if args.diff_file else collect_git_diff(
        args.repo, args.base, args.head, args.cached
    )
    prd_text = read_text(args.prd) if args.prd else ""
    result = analyze_scan(diff_text, prd_text)

    rendered = (
        json.dumps(result, ensure_ascii=False, indent=2)
        if args.format == "json"
        else render_markdown(result)
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
