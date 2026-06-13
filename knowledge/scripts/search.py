"""Knowledge base search.

BM25 retrieval over the index built by build_index.py. No external deps.

Usage:
  python search.py "登录失败"
  python search.py "密码强度" --top-k 5
  python search.py "退款" --source historical-cases
  python search.py "登录" --json           # machine-readable output
  python search.py "登录" --trigger         # simulate Skill trigger detection

Returns ranked sections with file/heading/snippet. Designed to be the
'retrieval half' of the v1 knowledge base; integration with Skill phases
happens at the prompt level (see docs/architecture/knowledge-base.md).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from build_index import (
    BM25_B,
    BM25_K1,
    PRIORITY_WEIGHT,
    strip_heading_marker,
    tokenize,  # re-used to keep tokenization consistent
)

SCRIPT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = SCRIPT_DIR.parent
INDEX_PATH = KNOWLEDGE_DIR / "index.json"

# Trigger keywords — when matched, the Skill should auto-invoke this search.
TRIGGER_KEYWORDS: dict[str, list[str]] = {
    "domain-glossary": [
        "术语表", "术语", "查术语", "glossary", "什么是",
        "定义", "名词解释", "业务概念",
    ],
    "project-conventions": [
        "按规范", "项目规范", "规范", "命名规则", "命名规范",
        "convention", "标准", "约定", "错误码",
    ],
    "historical-cases": [
        "参考历史", "查历史", "查历史用例", "历史用例", "类似用例",
        "复用", "历史", "回归用例", "已有用例", "historical",
    ],
    "*": [
        "查一下知识库", "查知识库", "搜知识库", "知识库里",
        "knowledge base", "kb:", "/kb",
    ],
}

# Snippet window around matched terms.
SNIPPET_CONTEXT = 80
SNIPPET_MAX_LEN = 320


# --- BM25 scoring ----------------------------------------------------------

def bm25_score(
    query_tokens: list[str],
    sec_id: str,
    term_freq: dict[str, dict[str, int]],
    doc_freq: dict[str, int],
    doc_len: dict[str, int],
    avg_doc_len: float,
    n_docs: int,
) -> float:
    """Standard BM25 Okapi scoring."""
    if not query_tokens or avg_doc_len <= 0:
        return 0.0

    score = 0.0
    sec_tf = term_freq.get(sec_id, {})
    sec_len = doc_len.get(sec_id, 0)
    for term in query_tokens:
        if term not in sec_tf:
            continue
        f = sec_tf[term]
        df = doc_freq.get(term, 0)
        # IDF with the +0.5 smoothing (Robertson / Zaragoza 2009).
        idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
        numerator = f * (BM25_K1 + 1)
        denominator = f + BM25_K1 * (1 - BM25_B + BM25_B * sec_len / avg_doc_len)
        score += idf * numerator / denominator
    return score


# --- Snippet rendering -----------------------------------------------------

def render_snippet(text: str, matched_terms: set[str]) -> str:
    """Pick a window around the first matched term; fall back to the head."""
    text_one_line = re.sub(r"\s+", " ", text).strip()
    if not text_one_line:
        return ""

    lower = text_one_line.lower()
    first_pos = len(text_one_line)
    for term in matched_terms:
        idx = lower.find(term)
        if 0 <= idx < first_pos:
            first_pos = idx

    if first_pos >= len(text_one_line):
        start = 0
    else:
        start = max(0, first_pos - SNIPPET_CONTEXT // 2)
    end = min(len(text_one_line), start + SNIPPET_MAX_LEN)
    snippet = text_one_line[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text_one_line):
        snippet = snippet + "…"
    return snippet


# --- Core search -----------------------------------------------------------

def search(
    query: str,
    index: dict,
    top_k: int = 5,
    source_filter: str | None = None,
) -> list[dict[str, Any]]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    inv = index["inverted_index"]
    term_freq = inv["term_freq"]
    doc_freq = inv["doc_freq"]
    doc_len = inv["doc_len"]
    avg_doc_len = inv["avg_doc_len"]
    n_docs = len(term_freq)

    # Index by sec_id -> source for filter + metadata.
    sec_to_source: dict[str, dict] = {}
    for src in index["sources"]:
        for sec_idx in range(len(src["sections"])):
            sec_id = f"{src['filename']}#{sec_idx}"
            sec_to_source[sec_id] = src

    if source_filter:
        sec_to_source = {
            sid: src for sid, src in sec_to_source.items()
            if src["filename"].startswith(source_filter)
        }

    matched_terms = set(query_tokens)
    results: list[dict[str, Any]] = []
    for sec_id in sec_to_source:
        score = bm25_score(
            query_tokens, sec_id, term_freq, doc_freq, doc_len, avg_doc_len, n_docs
        )
        if score <= 0:
            continue
        src = sec_to_source[sec_id]
        sec_idx = int(sec_id.rsplit("#", 1)[1])
        section = src["sections"][sec_idx]
        priority_weight = PRIORITY_WEIGHT.get(src.get("priority", "normal"), 1.0)
        # Strip the `###h:` marker before rendering the snippet.
        raw_text = strip_heading_marker(section["text"])
        results.append({
            "score": round(score * priority_weight, 4),
            "filename": src["filename"],
            "title": src["title"],
            "heading": section["heading"],
            "priority": src.get("priority", "normal"),
            "tags": src.get("tags", []),
            "snippet": render_snippet(raw_text, matched_terms),
            "matched_terms": sorted(matched_terms & set(tokenize(raw_text))),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


# --- Trigger detection -----------------------------------------------------

def detect_trigger(text: str) -> dict[str, Any]:
    """Return which knowledge source should be retrieved given the user's text."""
    text_lower = text.lower()
    matched: dict[str, list[str]] = {}
    for source, kws in TRIGGER_KEYWORDS.items():
        hits = [kw for kw in kws if kw.lower() in text_lower]
        if hits:
            matched[source] = hits
    return {"triggers": matched}


# --- Output formatting -----------------------------------------------------

def format_text(results: list[dict], query: str) -> str:
    if not results:
        return f"知识库中没有找到与「{query}」相关的内容。"
    lines = [f"知识库检索: 「{query}」 (命中 {len(results)} 条)", ""]
    for i, r in enumerate(results, 1):
        lines.append(f"--- #{i}  score={r['score']}  source={r['filename']}  priority={r['priority']} ---")
        lines.append(f"  title:   {r['title']}")
        lines.append(f"  heading: {r['heading']}")
        if r["tags"]:
            lines.append(f"  tags:    {', '.join(r['tags'])}")
        lines.append(f"  matched: {', '.join(r['matched_terms'])}")
        lines.append(f"  snippet: {r['snippet']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the knowledge base")
    parser.add_argument("query", help="search query (Chinese or English)")
    parser.add_argument("--top-k", type=int, default=5, help="number of results (default 5)")
    parser.add_argument(
        "--source",
        default=None,
        help="filter by source filename prefix (e.g. historical-cases)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument(
        "--trigger",
        action="store_true",
        help="also show which triggers matched in the query",
    )
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(
            f"[error] index.json not found at {INDEX_PATH}. "
            f"Run build_index.py first.",
            file=sys.stderr,
        )
        return 1

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    results = search(
        args.query,
        index,
        top_k=args.top_k,
        source_filter=args.source,
    )

    if args.json:
        payload: dict[str, Any] = {"query": args.query, "results": results}
        if args.trigger:
            payload["trigger"] = detect_trigger(args.query)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    out = format_text(results, args.query)
    print(out)
    if args.trigger:
        trig = detect_trigger(args.query)
        if trig["triggers"]:
            print("\n触发词命中:")
            for source, kws in trig["triggers"].items():
                print(f"  [{source}] -> {', '.join(kws)}")
        else:
            print("\n(无触发词命中 — 此次检索属于手动调用)")
    return 0 if results else 2


if __name__ == "__main__":
    sys.exit(main())
