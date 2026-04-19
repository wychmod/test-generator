# OpenClaw Skill Adapter

This is a minimal adapter for OpenClaw-style or compatible hosts.

## Skill Purpose

Generate structured and reviewable test design outputs from requirements, PRDs, APIs, source code, bugfix context, or workflow descriptions.

## Trigger Situations

Use when the user asks to:
- generate test cases
- expand test scenarios
- review testcase quality
- derive MBT-oriented testing outputs
- standardize testing documents

## Required Files

- `SKILL.md`
- `resources/quality_checklist.md`
- `templates/testcase_template.md`

## Optional Files

- `prompts/phase0_input_preprocessing_prompt.md`
- `prompts/phase1_requirements_prompt.md`
- `prompts/phase2_code_analysis_prompt.md`
- `prompts/phase3_domain_analysis_prompt.md`
- `prompts/phase4_mbt_design_prompt.md`
- `prompts/phase5_testcase_generation_prompt.md`
- `scripts/prd_reader.py`

## Fallback

If the host cannot execute scripts or load all files:
- use text-based analysis only
- produce lightweight structured outputs
- record assumptions and blockers explicitly

## Canonical Source

The repository root remains the canonical source. This adapter only provides a minimal host-facing entry.
