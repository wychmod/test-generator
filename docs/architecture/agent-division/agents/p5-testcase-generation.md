# P5 Agent 契约 — 用例生成

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase5_testcase_generation_prompt.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p5-testcase-generation` |
| 角色 | 测试用例设计专家 + 测试自动化架构师 |
| 对应能力 | 结构化测试用例生成、追溯矩阵与质量门禁 |
| 可跳过 | **否** —— 流水线终点 |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

专业面：等价类划分、边界值分析、因果图、正交试验、场景法；
JUnit / Pytest / Robot / Cypress / Postman 等多框架适配。

---

## 2. 输入契约

P5 是**汇聚点**，按执行路径消费上游产物：

| 输入 | 来源 | 用途 |
|---|---|---|
| `[参考知识]` 区块 | P0 规范化产物 | 术语、规范、历史用例参考（**不可**直接改写成新需求） |
| 可测试需求 | P1 的 `02_testable_requirements.md` | 用例覆盖对象 |
| 边界条件 | P1 的 `03_boundary_conditions.md` | 边界用例来源 |
| 代码缺陷与契约 | P2 的 `03_defect_radar.md` / `05_contract_test_derivation.md` | 反向测试与契约用例 |
| 测试模型与覆盖准则 | P4 全部产物 | 生成蓝图 |

**Step 0（`[参考知识]` 处理）**：知识库中的历史用例只能作为
术语、规范、边界候选或历史参考，**不得**直接改写成新需求。

---

## 3. 执行流程

指向 prompt 的核心执行章（Step 1-5）：

| Step | 内容 |
|---|---|
| Step 1 | 测试用例生成（含用例 ID 命名、分类体系、标准模板） |
| Step 2 | 用例集合组织与统计 |
| Step 3 | 双向追溯矩阵（RTCM / CTRM + 缺口分析） |
| Step 4 | 用例去重与优化 |
| Step 5 | 自动化适配建议 |

**v2.1 增强章节**：

| 章 | 内容 | 写入 |
|---|---|---|
| §6 | 混沌工程场景 (Chaos Engineering) | `04_chaos_engineering_scenarios.md` |
| §7 | 测试数据工厂模式 (Test Data Factory) | `05_test_data_strategy.md` |

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `01_testcase_collection.md` | **总是** | 最终交付 |
| `02_test_suite_summary.md` | **总是** | 最终交付 |
| `03_traceability_matrix.md` | **总是** | 最终交付 |
| `04_chaos_engineering_scenarios.md` | 高可用要求系统 | 最终交付 |
| `05_test_data_strategy.md` | 需要可复用测试数据 | 最终交付 |

**ID 命名空间**：`TC`（测试用例），格式
`TC-{PHASE}-{MODULE}-{SEQ:03d}`，如 `TC-AUTH-LOGIN-001`。

> **注意编号语义陷阱**：`TC-` 中的 `PHASE` 是**功能域**缩写
> （AUTH / ORDER / PAY），不是流水线阶段号 0-5。两者不要混淆。

**质量报告**：`quality_report.md` 是**编排者**产出的全局产物，
不属于本 agent —— 它需要跨阶段汇总 P0-P5 的评分，让 P5 自己写
会天然偏向自己那一环。

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `SC5-*` | 本 prompt 的「质量门禁」章 |
| 量化评分 | `G5-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 90 —— 这是**最高档**，且对应
`devtools/skill_quality_audit.py` 的 `FORMAL_SCORE_THRESHOLD`。

**只有达到 90 分，产物才可声明为"正式测试用例"**；低于阈值只能
交付草稿，且必须按「风险摘要 → 缺失信息清单 → 降级草稿」的顺序说明。

**必须通过项（摘要）**：

| ID | 检查项 | 标准 |
|---|---|---|
| `SC5-1` | 需求覆盖完整 | 100% 的可测试需求至少被一个用例覆盖 |
| `SC5-2` | 边界覆盖完整 | P1 中所有 BV 和 EP 都有对应用例 |
| `SC5-3` | 路径覆盖达标 | P4 最小测试集中的所有路径都有用例 |

---

## 6. 降级与交接

### 降级路径

- 需求覆盖不全 → 向编排者请求回退到 P1
- 上游产物缺失时**不得**凭空编造需求或预期结果；必须推断时明确标记

### 交接

```
P1/P2/P3/P4 ──► P5 ──► review（独立评审）──► 最终交付
```

**P5 是生产链的终点，不是质量的责任终点。** 交付前的评审由
独立评审 agent 执行（见 [`../review-agent.md`](../review-agent.md)）——
裁判席不在自己辖区里。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase5_testcase_generation_prompt.md`](../../../../skills/testcase-generator/prompts/phase5_testcase_generation_prompt.md)
- 用例格式：[`../../../../skills/testcase-generator/resources/testcase_formats.md`](../../../../skills/testcase-generator/resources/testcase_formats.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
