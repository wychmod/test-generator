# Architecture — 架构总览

> 本目录描述 testcase-generator 的设计意图、模块边界和数据流。

## 本目录已有文档

- ✅ [`pipeline-overview.md`](pipeline-overview.md)：六阶段流水线详解
- ✅ [`knowledge-base.md`](knowledge-base.md)：本地知识库（触发式 BM25）
- ✅ [`incremental-code-analysis-design.md`](incremental-code-analysis-design.md)：增量代码分析设计
- ✅ [`skill-ecosystem-benchmark.md`](skill-ecosystem-benchmark.md)：Skill 生态对标与改进方案（Agent Skills / Agent Plugins / 多客户端组织方式）

## 待写内容

- [ ] **data-model.md**：核心数据结构（需求条目 / 用例条目 / 追溯矩阵 / 状态机）
- [ ] **prompts-vs-templates.md**：`skills/testcase-generator/prompts/` 与 `skills/testcase-generator/templates/` 的职责边界
- [ ] **quality-gate-flow.md**：阶段间质量门禁如何触发、各阶段产物的最低验收标准

## 已有的设计源（散落各处）

- 入口契约：[`../../skills/testcase-generator/SKILL.md`](../../skills/testcase-generator/SKILL.md)
- 六阶段能力声明：[`../../skill.manifest.json`](../../skill.manifest.json) → `核心能力` 字段
- 阶段产物协议：[`../../skills/testcase-generator/resources/output_artifacts.md`](../../skills/testcase-generator/resources/output_artifacts.md)
- 质量基线：[`../quality/test-plan.md`](../quality/test-plan.md)

## 相关工具

- 预检审计：[`../../devtools/capability_audit.py`](../../devtools/capability_audit.py)
- 质量审计：[`../../devtools/skill_quality_audit.py`](../../devtools/skill_quality_audit.py)
- 文档一致性审计：[`../../.harness/scripts/doc_consistency_audit.py`](../../.harness/scripts/doc_consistency_audit.py)
