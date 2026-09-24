# P4 Agent 契约 — MBT 设计

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase4_mbt_design_prompt.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p4-mbt-design` |
| 角色 | MBT（基于模型的测试）架构师 + 测试设计专家 |
| 对应能力 | MBT 导向测试设计 |
| 可跳过 | 是（无状态模型需求时可跳过） |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

专业面：ISTQB Advanced Level Test Analyst 认证级能力、状态机测试、
组合测试、分类树法（CTT）。

---

## 2. 输入契约

| 输入 | 来源 |
|---|---|
| 测试模型变量来源 | P1 的 `02_testable_requirements.md` / `03_boundary_conditions.md` |
| 领域模型 | P3 的 `01_business_domain_model.md` / `02_state_machine_spec.md` / `03_test_parameter_space.md` |
| 增强模型信息 | P3 的 `04_event_storming_model.md` / `05_temporal_constraints.md`（如适用） |

**启用条件**：用户需要基于模型生成测试；系统状态复杂，单靠手工列举容易漏测。

---

## 3. 执行流程

指向 prompt 的核心执行章。要点：

- 定义测试对象（Test Object）与变量
- 枚举状态转换路径
- 计算最小测试集（Minimal Test Set）
- 建立覆盖准则与优先级策略

**v2.1 增强章节**：

| 章 | 内容 | 写入 |
|---|---|---|
| §6 | 变异测试策略 (Mutation Testing Strategy) | `04_mutation_testing_strategy.md` |
| §7 | 错误猜测法集成 (Error Guessing) | `05_error_guessing_checklist.md` |

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `01_test_model_specification.md` | **总是** | P5 |
| `02_state_transition_graph.md` | **总是** | P5 |
| `03_coverage_criteria.md` | **总是** | P5 |
| `04_mutation_testing_strategy.md` | 需要评估用例有效性 | P5 |
| `05_error_guessing_checklist.md` | 需要补充经验性场景 | P5 |

**ID 命名空间**：`TO`（测试对象） / `TS`（测试状态） / `TT`（转换） /
`PATH`（路径） / `MTS`（变异策略）

**文件头关键字段**：`total_test_objects`、`total_paths_enumerated`、
`minimal_test_set_size`、`target_coverage_level`、`estimated_coverage`。

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `SC4-*` | 本 prompt 的「质量门禁」章 |
| 量化评分 | `G4-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 85（与 P3 同档——设计错误同样会向下游全面传播）

---

## 6. 降级与交接

### 降级路径

- 输入的领域模型不完整 → **不自行补模型**，向编排者请求回退到 P3
- 状态空间爆炸（枚举不可行）→ 降级为抽样策略，并显式声明覆盖率上限

### 交接

```
P3 ──► P4 ──► P5（消费全部 P4 产物）
```

**P4 是唯一"纯设计"阶段**：它的产物不是给用户看的，而是 P5 的
生成蓝图。若 P4 与 P5 合并为一个 agent，可以省一次交接，代价是
丢失独立的覆盖准则评审点。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase4_mbt_design_prompt.md`](../../../../skills/testcase-generator/prompts/phase4_mbt_design_prompt.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
