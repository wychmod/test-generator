"""Smoke tests for ingest.py — no LLM call required.

Validates: sensitive-pattern detection, frontmatter parsing, output
validation. Run with `python test/test_ingest_smoke.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the skill's knowledge/scripts directory importable.
# 技能运行时内容位于 skills/testcase-generator/（Agent Skills 标准布局）
SKILL_DIR = "skills/testcase-generator"
SCRIPT_DIR = Path(__file__).resolve().parent
KB_SCRIPTS = SCRIPT_DIR.parent / SKILL_DIR / "knowledge" / "scripts"
sys.path.insert(0, str(KB_SCRIPTS))

import ingest  # noqa: E402


def test_check_sensitive_clean():
    assert ingest.check_sensitive("hello world") is None
    assert ingest.check_sensitive("UID-000123 is a user id") is None


def test_check_sensitive_aws_key():
    text = "AWS key is AKIAIOSFODNN7EXAMPLE"
    out = ingest.check_sensitive(text)
    assert out is not None
    assert "[敏感" in out


def test_check_sensitive_openai_key():
    text = "use this key: sk-proj-abcdefghij1234567890abcdefghij"
    out = ingest.check_sensitive(text)
    assert out is not None


def test_check_sensitive_github_pat():
    text = "ghp_" + "x" * 40
    assert ingest.check_sensitive(text) is not None


def test_check_sensitive_pan_like():
    text = "card 4111111111111111"
    assert ingest.check_sensitive(text) is not None


def test_validate_output_happy_path():
    md = """---
title: 测试条目
slug: test-entry
category: domain-glossary
tags: [test, glossary]
priority: normal
source_type: text
source_origin: unit test
---

# 测试条目

## 术语

定义内容。
"""
    fm, body = ingest.validate_output(md)
    assert fm["title"] == "测试条目"
    assert fm["slug"] == "test-entry"
    assert fm["category"] == "domain-glossary"
    assert fm["priority"] == "normal"
    assert body.startswith("# 测试条目")


def test_validate_output_missing_frontmatter():
    md = "# 标题\n\n无 frontmatter 的内容"
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "frontmatter" in str(exc).lower() or "YAML" in str(exc)


def test_validate_output_bad_slug():
    md = """---
title: Bad Slug
slug: BAD SLUG!
category: domain-glossary
tags: [t]
priority: normal
---

# Bad Slug

content
"""
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "slug" in str(exc).lower()


def test_validate_output_bad_category():
    md = """---
title: Bad Category
slug: bad-cat
category: unknown-category
tags: [t]
priority: normal
---

# Bad

content
"""
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "category" in str(exc).lower()


def test_validate_output_bad_priority():
    md = """---
title: Bad Priority
slug: bad-pri
category: domain-glossary
tags: [t]
priority: critical
---

# Bad

content
"""
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "priority" in str(exc).lower()


def test_validate_output_missing_field():
    md = """---
title: Missing
slug: missing
category: domain-glossary
---

# Missing

content
"""
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "tags" in str(exc) or "priority" in str(exc)


def test_validate_output_body_must_start_with_h1():
    md = """---
title: No H1
slug: no-h1
category: domain-glossary
tags: [t]
priority: normal
---

## 跳过了 H1

content
"""
    try:
        ingest.validate_output(md)
        assert False, "should have raised"
    except ValueError as exc:
        assert "#" in str(exc) or "h1" in str(exc).lower() or "h" in str(exc).lower()


if __name__ == "__main__":
    failures = 0
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL {fn.__name__}: {exc}")
        except Exception as exc:
            failures += 1
            print(f"  ERR  {fn.__name__}: {exc}")
    print(f"\n{len(tests)} tests, {failures} failures")
    sys.exit(1 if failures else 0)
