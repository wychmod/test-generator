# Codex Adapter for Testcase Generator

This file is a thin host adapter for Codex-style environments.

## Purpose

Use this adapter when the host expects an `AGENTS.md`-style engineering entry and needs to generate or review software test cases from:
- requirements
- PRDs
- API specifications
- source code
- bugfix context
- workflow descriptions

## Read These Files First

1. Root `SKILL.md`
2. `resources/quality_checklist.md`
3. `templates/testcase_template.md`
4. Relevant `prompts/phase*.md` files depending on task depth

## When to Use

Trigger for requests such as:
- generate structured test cases
- review or expand existing test cases
- analyze testing gaps from requirements or code
- produce MBT-oriented testing outputs
- standardize testcase documentation

## Fallback Behavior

If the environment cannot execute local scripts:
- ignore `scripts/prd_reader.py`
- work from text content only
- mark inferred assumptions explicitly

If the environment cannot navigate multiple files reliably:
- prioritize `SKILL.md`
- then `resources/quality_checklist.md`
- keep output lightweight and reviewable

## Notes

The canonical source remains the repository root. This adapter does not redefine the core methodology; it only adapts the entry shape for Codex-style hosts.
