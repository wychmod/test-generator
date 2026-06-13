"""Knowledge base ingest pipeline.

Reads source material (PDF / Markdown / TXT / image / pasted text), asks an
LLM (via a user-provided shell command) to extract a structured knowledge
entry, writes it to `knowledge/sources/<slug>.md`, and triggers an index
rebuild.

Why a shell command instead of an SDK:
  - Zero hard dependency on a specific LLM provider (openai, anthropic, ...)
  - User controls API keys, model choice, and routing entirely
  - Works offline with local models (ollama, vllm, llama.cpp)
  - Same code path runs in CI, on a developer laptop, and behind a corporate
    gateway — only the command changes

Configure via env var:
  TEST_GEN_LLM_CMD='openai api chat.completions.create -m gpt-4o -o /tmp/out.json ...'
  Or use a wrapper script: TEST_GEN_LLM_CMD='~/bin/my-llm-wrapper'

The command must read the source material from STDIN and write the LLM
response (Markdown with YAML frontmatter) to STDOUT. See README.md for
wrapper script examples.

Usage:
  python ingest.py path/to/spec.pdf
  python ingest.py path/to/spec.pdf --slug payment-glossary
  python ingest.py path/to/spec.pdf --dry-run         # show extraction only
  cat notes.md | python ingest.py -                     # ingest from stdin
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths relative to this script so it works from any cwd.
SCRIPT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = SCRIPT_DIR.parent
SOURCES_DIR = KNOWLEDGE_DIR / "sources"
PROMPT_PATH = Path(KNOWLEDGE_DIR).parent / "prompts" / "knowledge_ingest_prompt.md"

# --- LLM invocation --------------------------------------------------------

LLM_CMD_ENV = "TEST_GEN_LLM_CMD"

# Files we will NOT try to ingest (binary, oversized, etc.).
MAX_TEXT_BYTES = 5 * 1024 * 1024  # 5 MB raw text cap
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB image cap

# Patterns we refuse to ingest (P0 safety; user must scrub first).
_SENSITIVE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),                    # OpenAI key (incl. proj-)
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),                           # Anthropic API key
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),                              # GitHub PAT
    re.compile(r"gho_[A-Za-z0-9]{30,}"),                              # GitHub OAuth
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"\b\d{16,19}\b"),                                       # long digit runs (likely PAN)
]
_SENSITIVE_HINT = (
    "[敏感: 检测到疑似凭证/密钥/PAN 等敏感信息。已拒绝录入。请先脱敏后重试。]"
)

# Frontmatter sanity check.
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL
)


# --- Source extraction -----------------------------------------------------

def read_source(path: Path) -> tuple[str, str]:
    """Read a source file and return (source_type, text).

    Supports: .md / .markdown / .txt / .pdf (best effort) / images.
    """
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown", path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".txt":
        return "text", path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        return "pdf", _extract_pdf_text(path)
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        text = _extract_image_text(path)
        return ("image", text) if text else ("image", _ocr_missing_hint(path))
    raise ValueError(f"unsupported file type: {suffix}")


def _extract_pdf_text(path: Path) -> str:
    """Best-effort PDF text extraction. Returns a hint if no library."""
    try:
        import pypdf  # noqa: WPS433
    except ImportError:
        try:
            import PyPDF2  # noqa: WPS433
            reader = PyPDF2.PdfReader(str(path))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            return (
                f"[PDF: {path.name} - pypdf/PyPDF2 not installed.\n"
                f"Install: pip install pypdf, then retry.\n"
                f"Or convert to .md / .txt first.]"
            )
    reader = pypdf.PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_image_text(path: Path) -> str:
    """Best-effort image OCR via pytesseract. Returns '' if missing."""
    try:
        import pytesseract  # noqa: WPS433
        from PIL import Image  # noqa: WPS433
    except ImportError:
        return ""
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang="chi_sim+eng")


def _ocr_missing_hint(path: Path) -> str:
    return (
        f"[Image: {path.name} - OCR unavailable or empty.\n"
        f"Install: pip install pytesseract pillow, plus system tesseract-ocr "
        f"with Chinese language pack.\n"
        f"Or paste the image text directly.]"
    )


# --- Safety ----------------------------------------------------------------

def check_sensitive(text: str) -> str | None:
    """Return a hint if sensitive patterns are detected, else None."""
    for pat in _SENSITIVE_PATTERNS:
        if pat.search(text):
            return _SENSITIVE_HINT
    return None


# --- LLM call --------------------------------------------------------------

def call_llm(prompt: str, source_text: str, source_type: str) -> str:
    """Run the user-configured LLM command, returning its stdout as Markdown.

    The command must accept the prompt + source material on STDIN and return
    the model's Markdown output on STDOUT.
    """
    cmd = os.environ.get(LLM_CMD_ENV)
    if not cmd:
        raise RuntimeError(
            f"Environment variable {LLM_CMD_ENV} is not set.\n"
            f"Configure your LLM invocation command, e.g.:\n"
            f"  export {LLM_CMD_ENV}='openai api chat.completions.create ...'\n"
            f"Or use a wrapper script: TEST_GEN_LLM_CMD='~/bin/my-llm-wrapper'"
        )

    payload = f"{prompt}\n\n---\n\n# Source material (type={source_type})\n\n{source_text}\n"
    proc = subprocess.run(
        cmd,
        input=payload,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"LLM command failed (exit code {proc.returncode}):\n"
            f"  stdout: {proc.stdout[:500]}\n"
            f"  stderr: {proc.stderr[:500]}"
        )
    return proc.stdout


# --- Output validation -----------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")


def parse_frontmatter(md: str) -> tuple[dict, str]:
    """Extract YAML-ish frontmatter; keep body text."""
    m = _FRONTMATTER_RE.match(md)
    if not m:
        raise ValueError("LLM output missing YAML frontmatter (must start with `---`)")
    fm_block = m.group(1)
    body = md[m.end():]
    fm: dict = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        if key == "tags" and value.startswith("[") and value.endswith("]"):
            value = [
                t.strip().strip('"').strip("'")
                for t in value[1:-1].split(",") if t.strip()
            ]
        fm[key.strip()] = value
    return fm, body


def validate_output(md: str) -> tuple[dict, str]:
    """Validate LLM output structure. Raises on malformed."""
    fm, body = parse_frontmatter(md)
    required = ["title", "slug", "category", "tags", "priority"]
    missing = [k for k in required if k not in fm]
    if missing:
        raise ValueError(f"LLM output missing frontmatter fields: {', '.join(missing)}")

    slug = str(fm["slug"])
    if not _SLUG_RE.match(slug):
        raise ValueError(
            f"invalid slug: {slug!r} (must be kebab-case, all lowercase + hyphens, 2-41 chars)"
        )

    if fm["category"] not in {
        "domain-glossary", "project-conventions", "historical-cases",
        "compliance-rules", "api-quick-ref",
    }:
        raise ValueError(f"invalid category: {fm['category']}")

    if fm["priority"] not in {"high", "normal", "low"}:
        raise ValueError(f"invalid priority: {fm['priority']}")

    if not body.strip().startswith("# "):
        raise ValueError("body must start with `# <title>`")

    # Fill in ingestion-time metadata if missing.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fm.setdefault("ingested_at", today)
    fm.setdefault("updated", today)
    return fm, body


# --- File write ------------------------------------------------------------

def _stable_filename(slug: str) -> Path:
    return SOURCES_DIR / f"{slug}.md"


def write_entry(slug: str, fm: dict, body: str) -> Path:
    """Write (or overwrite) the knowledge entry. Returns the path."""
    fm_lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(str(v) for v in value) + "]"
        else:
            rendered = str(value)
        fm_lines.append(f"{key}: {rendered}")
    fm_lines.append("---")
    fm_lines.append("")
    full = "\n".join(fm_lines) + body
    if not full.endswith("\n"):
        full += "\n"
    out = _stable_filename(slug)
    out.write_text(full, encoding="utf-8")
    return out


def rebuild_index() -> None:
    """Trigger index rebuild via build_index.py --rebuild."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "build_index.py"), "--rebuild"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print("[warn] build_index.py returned non-zero:", file=sys.stderr)
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
    else:
        for line in proc.stdout.splitlines():
            if line.startswith("[ok]"):
                print(line)


# --- Main ------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest knowledge into the local KB")
    parser.add_argument(
        "source", nargs="?",
        help="source file path (PDF/MD/TXT/IMG) or '-' for stdin",
    )
    parser.add_argument("--slug", help="override output slug (default: derive from title)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print LLM output without writing files",
    )
    parser.add_argument(
        "--no-rebuild", action="store_true",
        help="skip index rebuild (use when batching multiple ingests)",
    )
    args = parser.parse_args()

    if args.source is None:
        parser.error("missing required argument: source (use '-' for stdin)")

    # Read source
    if args.source == "-":
        text = sys.stdin.read()
        source_type = "text"
        display_name = "stdin"
    else:
        path = Path(args.source)
        if not path.exists():
            print(f"[error] file not found: {path}", file=sys.stderr)
            return 1
        if path.stat().st_size > MAX_TEXT_BYTES:
            print(f"[error] file too large (> {MAX_TEXT_BYTES} bytes)", file=sys.stderr)
            return 1
        source_type, text = read_source(path)
        display_name = path.name

    print(f"[ingest] source: {display_name} (type={source_type}, bytes={len(text)})")

    sensitive = check_sensitive(text)
    if sensitive:
        print(sensitive, file=sys.stderr)
        return 2

    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    try:
        output = call_llm(prompt, text, source_type)
    except RuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 3

    try:
        fm, body = validate_output(output)
    except ValueError as exc:
        print(f"[error] LLM output invalid: {exc}", file=sys.stderr)
        print("--- raw output (first 500 chars) ---", file=sys.stderr)
        print(output[:500], file=sys.stderr)
        return 4

    if args.slug:
        fm["slug"] = args.slug

    if args.dry_run:
        print("[dry-run] would write:")
        print(f"  path: knowledge/sources/{fm['slug']}.md")
        print(f"  title: {fm['title']}")
        print(f"  category: {fm['category']}")
        print(f"  priority: {fm['priority']}")
        print(f"  tags: {fm['tags']}")
        print(f"  body length: {len(body)} chars")
        print("---")
        print(body[:500] + ("..." if len(body) > 500 else ""))
        return 0

    out = write_entry(fm["slug"], fm, body)
    print(
        f"[ok] wrote {out} ({len(body)} chars, "
        f"category={fm['category']}, priority={fm['priority']})"
    )

    if not args.no_rebuild:
        rebuild_index()
    else:
        print("[skip] index rebuild skipped (--no-rebuild); run build_index.py later")

    return 0


if __name__ == "__main__":
    sys.exit(main())
