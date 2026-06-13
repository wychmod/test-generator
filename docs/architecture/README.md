# Architecture — 架构总览

> 本目录描述 testcase-generator 的设计意图、模块边界和数据流。

## 待写内容

- [ ] **pipeline-overview.md**：六阶段流水线详解（输入预处理 → 需求 → 代码分析 → 领域建模 → MBT 设计 → 用例生成）
- [ ] **data-model.md**：核心数据结构（需求条目 / 用例条目 / 追溯矩阵 / 状态机）
- [ ] **prompts-vs-templates.md**：prompts/ 与 templates/ 的职责边界
- [ ] **quality-gate-flow.md**：阶段间质量门禁如何触发、各阶段产物的最低验收标准

## 已有的设计源（散落各处）

- 入口契约：[`../../SKILL.md`](../../SKILL.md)
- 六阶段能力声明：[`../../skill.manifest.json`](../../skill.manifest.json) → `核心能力` 字段
- 阶段产物协议：[`../../resources/output_artifacts.md`](../../resources/output_artifacts.md)
- 质量基线：[`../quality/test-plan.md`](../quality/test-plan.md)

## 相关工具

- 预检审计：[`../../devtools/capability_audit.py`](../../devtools/capability_audit.py)
- 质量审计：[`../../devtools/skill_quality_audit.py`](../../devtools/skill_quality_audit.py)
- 文档一致性审计：[`../../.harness/scripts/doc_consistency_audit.py`](../../.harness/scripts/doc_consistency_audit.py)
