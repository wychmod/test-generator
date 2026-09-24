# P3 Agent 契约 — 领域建模

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase3_domain_analysis_prompt.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p3-domain-modeling` |
| 角色 | 业务领域建模专家 + 测试数据架构师 |
| 对应能力 | 领域模型与状态模型构建 |
| 可跳过 | 是（简单 CRUD 需求不需要） |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

专业面：DDD 战略设计与战术建模、ERD、UML 类图、状态机建模、Event Storming。

---

## 2. 输入契约

| 输入 | 来源 |
|---|---|
| 需求条目 | P1 的 `02_testable_requirements.md` |
| 代码结构 / 数据流 | P2 的 `01_code_structure.md` / `02_data_flow_analysis.md`（若 P2 已执行） |

**启用条件**：存在状态流转、复杂规则、角色权限、生命周期管理。

---

## 3. 执行流程

指向 prompt 的核心执行章。要点：

- 业务实体与关系建模（ERD）
- 状态机规格（状态、事件、转换条件、非法路径）
- 参数空间与约束定义
- 不变量（Invariant）识别

**v2.1 增强章节**：

| 章 | 内容 | 写入 |
|---|---|---|
| §6 | 事件风暴 (Event Storming) 领域建模 | `04_event_storming_model.md` |
| §7 | 时序约束与时间相关业务规则 | `05_temporal_constraints.md`（Part A） |
| §8 | 跨系统集成点与接口契约 | `05_temporal_constraints.md`（Part B） |

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `01_business_domain_model.md` | **总是** | P4 |
| `02_state_machine_spec.md` | **总是** | P4（核心输入） |
| `03_test_parameter_space.md` | **总是** | P4 |
| `04_event_storming_model.md` | 存在领域事件 | P4、P5 |
| `05_temporal_constraints.md` | 存在时序/集成依赖 | P4、P5 |

**ID 命名空间**：`ENT`（实体） / `S`（状态） / `T`（转换） / `G`（守卫） /
`INV`（不变式） / `CMD`（命令） / `EVT`（事件） / `RM`（关系） / `UJM`（用户旅程）

> **`02_state_machine_spec.md` 是整个 MBT 链路的核心。** P4 的测试模型
> 直接以它为输入；若它不完整，P4 无法产出有效的最小覆盖集。

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `SC3-*` | 本 prompt 的「质量门禁」章（标注为 `SC<阶段>-<序号>` 命名空间） |
| 量化评分 | `G3-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 85（比 P1/P2 高一档——模型错误会向下游全面传播）

文件头含 `model_completeness_check` 字段：`PASSED` / `WARNINGS` / `FAILED`。

---

## 6. 降级与交接

### 降级路径

业务规则存在歧义时，**显式保留歧义**而不是悄悄猜测。
用 `[需确认]` 标注，并在状态机中以"待定转换"呈现。

### 交接

```
P1 ─┐
    ├─► P3 ──► P4 ──► P5
P2 ─┘
```

**P3 是 P4 的前置依赖。** 没有领域模型就没有测试模型。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase3_domain_analysis_prompt.md`](../../../../skills/testcase-generator/prompts/phase3_domain_analysis_prompt.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
