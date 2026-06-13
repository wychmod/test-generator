"""Knowledge base index builder.

Builds a lightweight BM25 index over `knowledge/sources/*.md` without
any external dependencies (no NLTK, no jieba, no embedding API).

Output: `knowledge/index.json` containing
  - sources: {filename: {title, tags, priority, mtime, sha, sections}}
  - inverted index + BM25 statistics

Why BM25 + custom tokenizer (not Embedding):
  - Zero external dependencies (works offline, across all AI hosts)
  - Deterministic (same input -> same output -> reproducible)
  - Transparent (index.json is human-readable / git-diffable)
  - Sufficient for structured testcase content (TC-ID + keyword matching is strong)

Usage:
  python build_index.py                # incremental (only if sources changed)
  python build_index.py --rebuild      # force rebuild
  python build_index.py --stats        # show index statistics
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

# Resolve paths relative to this script so it works from any cwd.
SCRIPT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = SCRIPT_DIR.parent
SOURCES_DIR = KNOWLEDGE_DIR / "sources"
INDEX_PATH = KNOWLEDGE_DIR / "index.json"

# --- Constants -------------------------------------------------------------

# Stopwords: tiny set for Chinese (jieba-free). Common function words that
# don't carry semantic weight in technical docs. NOT meant to be exhaustive.
STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没", "看",
    "好", "自己", "这", "那", "里", "为", "与", "等", "及", "或", "并", "但",
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "and", "or", "but", "if", "while", "that", "this", "these", "those",
    "it", "its", "they", "them", "their", "we", "us", "our",
}

# Priority multiplier (applied at search time, not index time).
PRIORITY_WEIGHT = {"high": 1.5, "normal": 1.0, "low": 0.7}

# BM25 parameters (Robertson / Zaragoza 2009 defaults).
BM25_K1 = 1.2
BM25_B = 0.75

# --- Tokenizer --------------------------------------------------------------

# Match: English words / TC-IDs / numbers / snake_case / kebab-case.
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}|[0-9]+|[\u4e00-\u9fa5]+")


def tokenize(text: str) -> list[str]:
    """Lightweight tokenizer: lowercase + split on word boundaries + drop stopwords."""
    tokens: list[str] = []
    for match in _TOKEN_RE.findall(text):
        t = match.lower()
        if t in STOPWORDS:
            continue
        if len(t) < 2 and not t.isdigit():
            # Drop single-char Chinese / single letters unless it's a digit.
            continue
        tokens.append(t)
    return tokens


# --- Section extraction -----------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-ish frontmatter; keep body text."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_block = m.group(1)
    body = text[m.end():]
    fm: dict = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        if key == "tags" and value.startswith("[") and value.endswith("]"):
            value = [t.strip().strip('"').strip("'") for t in value[1:-1].split(",") if t.strip()]
        fm[key.strip()] = value
    return fm, body


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split Markdown body on `##` headings. Returns [(heading, content), ...].

    The heading is also prepended to the content (with a `###h:` marker) so
    the tokenizer can match it. The raw heading text is still returned as the
    first element for display in search results.
    """
    raw_sections: list[tuple[str, str]] = []
    current_heading = "(intro)"
    current_lines: list[str] = []

    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                raw_sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        raw_sections.append((current_heading, "\n".join(current_lines)))

    # Prepend heading into the content so BM25 can score against it.
    return [
        (h, c if h == "(intro)" else f"###h: {h}\n\n{c}")
        for h, c in raw_sections
    ]


def strip_heading_marker(text: str) -> str:
    """Remove the `###h: ...` marker from a content string for snippet display."""
    if text.startswith("###h:"):
        return text.split("\n\n", 1)[1] if "\n\n" in text else ""
    return text


# --- Index building ---------------------------------------------------------

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_source(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fall back to gbk for files that slipped in as Windows-encoded.
        text = path.read_text(encoding="gbk", errors="replace")

    if not text.strip():
        return None

    fm, body = parse_frontmatter(text)
    title = fm.get("title") or path.stem
    priority = fm.get("priority", "normal").lower()
    if priority not in PRIORITY_WEIGHT:
        priority = "normal"
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    updated = fm.get("updated", "")

    sections = split_sections(body)

    return {
        "filename": path.name,
        "title": title,
        "tags": tags,
        "priority": priority,
        "updated": updated,
        "mtime": int(path.stat().st_mtime),
        "sha": sha256(text),
        "sections": [
            {"heading": h, "text": t.strip()} for h, t in sections if t.strip()
        ],
    }


def build_inverted_index(sources: list[dict]) -> tuple[dict, dict, dict]:
    """Build (term_freq, doc_freq, doc_len) for BM25."""
    term_freq: dict[str, Counter] = {}      # term -> Counter(sec_id -> count)
    doc_freq: dict[str, int] = {}           # term -> number of sections containing it
    doc_len: dict[str, int] = {}            # sec_id -> token count

    for src in sources:
        for sec_idx, section in enumerate(src["sections"]):
            sec_id = f"{src['filename']}#{sec_idx}"
            tokens = tokenize(section["text"])
            doc_len[sec_id] = len(tokens)
            tf: Counter[str] = Counter(tokens)
            term_freq[sec_id] = tf
            for term in set(tokens):
                doc_freq[term] = doc_freq.get(term, 0) + 1

    # Convert Counter to dict for JSON serialization.
    return (
        {sid: dict(c) for sid, c in term_freq.items()},
        doc_freq,
        doc_len,
    )


def build_index(rebuild: bool = False) -> dict:
    sources_meta: list[dict] = []
    for path in sorted(SOURCES_DIR.glob("*.md")):
        # Skip README (it's the usage guide, not a knowledge entry).
        # Skip files starting with `_` (templates / drafts that aren't ready).
        if path.name.lower() == "readme.md":
            continue
        if path.name.startswith("_"):
            continue
        meta = load_source(path)
        if meta is None:
            continue
        sources_meta.append(meta)

    if not sources_meta:
        print(f"[warn] no .md files found in {SOURCES_DIR}", file=sys.stderr)

    term_freq, doc_freq, doc_len = build_inverted_index(sources_meta)

    avg_doc_len = (sum(doc_len.values()) / len(doc_len)) if doc_len else 0.0

    index = {
        "version": 1,
        "built_at": datetime.utcnow().isoformat() + "Z",
        "sources": sources_meta,
        "inverted_index": {
            "term_freq": term_freq,
            "doc_freq": doc_freq,
            "doc_len": doc_len,
            "avg_doc_len": avg_doc_len,
            "k1": BM25_K1,
            "b": BM25_B,
        },
        "stats": {
            "num_sources": len(sources_meta),
            "num_sections": sum(len(s["sections"]) for s in sources_meta),
            "vocab_size": len(doc_freq),
            "avg_doc_len": round(avg_doc_len, 2),
        },
    }
    return index


def needs_rebuild() -> bool:
    if not INDEX_PATH.exists():
        return True
    try:
        existing = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    for src in existing.get("sources", []):
        path = SOURCES_DIR / src["filename"]
        if not path.exists():
            return True
        if int(path.stat().st_mtime) != src["mtime"]:
            return True
    return False


def print_stats(index: dict) -> None:
    s = index["stats"]
    print(f"  sources:    {s['num_sources']}")
    print(f"  sections:   {s['num_sections']}")
    print(f"  vocab:      {s['vocab_size']} terms")
    print(f"  avg_doc_len: {s['avg_doc_len']} tokens")
    print(f"  index file:  {INDEX_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build knowledge base index")
    parser.add_argument("--rebuild", action="store_true", help="force rebuild even if up to date")
    parser.add_argument("--stats", action="store_true", help="print index statistics and exit")
    args = parser.parse_args()

    if not SOURCES_DIR.exists():
        print(f"[error] sources directory not found: {SOURCES_DIR}", file=sys.stderr)
        return 1

    if args.stats:
        if not INDEX_PATH.exists():
            print("[error] index.json not found; run without --stats first", file=sys.stderr)
            return 1
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        print_stats(index)
        return 0

    if not args.rebuild and not needs_rebuild():
        print("[ok] index is up to date (use --rebuild to force)")
        return 0

    print("[build] scanning sources...")
    index = build_index(rebuild=args.rebuild)
    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] index built -> {INDEX_PATH}")
    print_stats(index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
