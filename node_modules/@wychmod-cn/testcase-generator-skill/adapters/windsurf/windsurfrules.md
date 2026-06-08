# Windsurf Rules — testcase-generator (soft adapter)

> This file is a **soft adapter** for Windsurf / Antigravity (Codeium, Google). These editors do not consume a `SKILL.md`-style skill entry; they consume a single rules file at the project root: `.windsurfrules`. The npm activation command in this repository will copy this file as `.windsurfrules` so the editor can pick it up automatically.
>
> Repository canonical source: the root `SKILL.md` and the six-phase pipeline in `prompts/`. This adapter does not redefine the methodology — it only tells the editor **when** to engage, **which files to read in which order**, and **how to degrade** when context is limited.

## When to engage

Engage the testcase-generator workflow when the user asks Windsurf / Antigravity to:

- generate test cases from requirements, PRD, API spec, user story, or natural-language description
- review, expand, audit, or standardize existing test cases or test scenarios
- derive MBT-oriented test design (state machines, transition coverage, decision tables)
- combine source code with requirements to back-fill missing test paths or contract risks
- produce traceability matrices, quality gate reports, or test design artifacts

## Recommended reading order

1. Root `SKILL.md` — core rules, execution modes, quality gates, minimum delivery protocol.
2. `templates/testcase_template.md` — output shape for formal test cases.
3. `resources/quality_checklist.md` — quality gates to enforce before delivery.
4. Relevant `prompts/phase*.md` based on task depth:
   - `phase0_input_preprocessing_prompt.md` — input quality, gaps, ambiguity
   - `phase1_requirements_prompt.md` — testable requirements, boundary conditions
   - `phase2_code_analysis_prompt.md` — code/contract-assisted analysis
   - `phase3_domain_analysis_prompt.md` — domain & state models
   - `phase4_mbt_design_prompt.md` — coverage criteria, transition paths
   - `phase5_testcase_generation_prompt.md` — final testcase collection
5. `resources/output_artifacts.md` — what each phase should deliver.
6. `resources/testcase_formats.md` — choose Markdown / Gherkin / JSON / data-driven.

If the user provides a local PRD / Markdown / PDF, prefer running `scripts/prd_reader.py` when the editor can execute scripts.

## Working principles the editor must respect

- Never invent requirements, business rules, or expected results. If inference is required, mark it explicitly as "推断 / inferred" or "假设 / assumed".
- Always preserve traceability between the source (requirement / code) and the conclusion (testcase).
- Prefer executable steps and binary-observable expected results over prose.
- Distinguish "confirmed" vs "inferred" content in the output.
- When critical input is missing, surface the gap first; only then offer a degraded draft.
- If code behavior contradicts the requirements, treat code as the current implementation but call out the conflict.
- Quality over quantity — never pad the test suite with low-value duplicates.
- Once a term is defined, keep it consistent across the deliverable.

## Output style

- Lead with a short "Confirmed vs Inferred" split.
- Prefer structured tables for test cases (id, title, preconditions, data, steps, expected, priority, type, traceability, assumptions).
- For BDD, use Gherkin (Feature / Scenario / Given-When-Then) with observable `Then` clauses.
- For API/contract work, include request, expected response, status code, schema checks, auth/permission branches, and an error matrix.
- For combinatorial inputs, use a data-driven layout and call out boundary / equivalence / pairwise strategy.

## Fallback strategy

When the editor is in a quick-reply mode, the context is tight, or the user explicitly asks for a lightweight result:

- Output a **test point list** or **scenario list** instead of full formal cases, and label it as "测试草稿 / test draft".
- Skip deep MBT/Phase 3–4 unless the user explicitly asks for state-machine-level design.
- Use Markdown table form (not Gherkin) to keep the output compact.
- Explicitly list missing inputs and assumed defaults.
- Never claim a degraded draft is a "正式测试用例 / formal test case".

If the editor cannot read the full repository or cannot execute `scripts/prd_reader.py`:

- Work from the text the user supplies in chat.
- Do not fabricate file contents.
- Mention which files you would normally consult but could not.

## Notes

- This is a soft adapter: the canonical methodology lives in the root `SKILL.md`. Treat this file as a routing hint, not a substitute.
- The npm `test-generator activate windsurf` command copies this file as `.windsurfrules` at the project root (or under the user's home directory with `-g`).
- The Chinese original of the methodology remains authoritative; English content here is for editor English-first context.
- If multiple AI hosts (Claude / Qoder / CodeBuddy / Trae / Cursor) are configured for the same repo, prefer the canonical `SKILL.md` for the active host — `.windsurfrules` only applies when Windsurf or Antigravity is the active tool.
