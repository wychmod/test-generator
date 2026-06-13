# Quality — 质量与评测

> 测试计划、质量门禁、回归基线、评审 checklist。

## 现有文档

- [`test-plan.md`](test-plan.md) — 评测维度、行业基准（ISO/IEC/IEEE 29119-3 / Azure Test Plans / Cucumber Gherkin / ISTQB）

## 待写内容

- [ ] **quality-gates.md**：阶段间质量门禁如何触发、各阶段产物的最低验收标准、评分阈值
- [ ] **review-checklist.md**：人工评审一份 testcase 输出时的 checklist
- [ ] **regression-baseline.md**：`.harness/eval/baselines/` 下的基线用例如何维护、何时该更新

## 评测流水线

评测流水线由 `.harness/eval/run_eval.py` 驱动，产出报告写到 `.harness/eval/HEALTH_REPORT.md`。基线用例存放于 `.harness/eval/baselines/`，**任何对 prompts/ 或 templates/ 的修改都必须同步更新基线**。

## 与 devtools/ 的关系

- [`../../devtools/skill_quality_audit.py`](../../devtools/skill_quality_audit.py) — 单元级审计（每个产物文件单独评分）
- [`../../.harness/eval/run_eval.py`](../../.harness/eval/run_eval.py) — 端到端评测（基线输入 → Skill 输出 → 评分）

两者的关系：unit audit 决定「这个 Skill 文件本身合格吗」，e2e eval 决定「用这个 Skill 跑出来的东西合格吗」。
