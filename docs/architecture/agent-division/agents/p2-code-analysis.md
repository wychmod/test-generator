# P2 Agent 契约 — 代码分析

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase2_code_analysis_prompt.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p2-code-analysis` |
| 角色 | 高级软件测试架构师 + 静态代码分析专家 |
| 对应能力 | 代码与接口契约辅助分析 |
| 可跳过 | 是（仅需求文档输入时可跳过） |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

专业面：多语言静态分析（Java/Python/JavaScript/Go/C#/TypeScript/Rust）、
McCabe 圈复杂度、Halstead 度量。

---

## 2. 输入契约

| 输入 | 来源 |
|---|---|
| 源代码 / 接口实现 / API 定义 | 用户直接提供（经 P0 规范化） |
| 需求条目（用于 PRD 符合性比对） | P1 的 `02_testable_requirements.md`（若 P1 已执行） |
| 增量上下文（base / head） | 用户提供，用于增量模式 |

**分析模式**（写入文件头 `analysis_mode` 字段）：

`actual_analysis` / `contract_analysis` / `logical_modeling` /
`hybrid_analysis` / `incremental_analysis` / `incremental_hybrid_analysis`

---

## 3. 执行流程

指向 prompt 的核心执行章。要点：

- 模块结构与调用关系梳理
- 数据流图（DFD）构建
- 缺陷雷达扫描（脆弱逻辑、未处理异常、安全检查）
- 需求-代码映射（当有 P1 产物时）

**v2.1 增强章节**：

| 章 | 内容 | 写入 |
|---|---|---|
| §8 | 并发分析与竞态条件检测 | `04_concurrency_analysis.md` |
| §9 | API 契约测试推导 (Contract-First Testing) | `05_contract_test_derivation.md` |
| §10 | 技术债务识别与评估 | 并入 `03_defect_radar.md`，不单独成文件 |

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `00_incremental_scope.md` | 增量模式适用 | P5 |
| `01_code_structure.md` | **总是** | P3、P4 |
| `02_data_flow_analysis.md` | **总是** | P3、P4 |
| `03_defect_radar.md` | **总是**（含技术债务章） | P5 |
| `04_concurrency_analysis.md` | 存在并发场景 | P5 |
| `05_contract_test_derivation.md` | 有 API 定义 | P5 |

**ID 命名空间**：`DEF`（缺陷） / `DF`（数据流） / `FUNC`（函数） /
`PATH`（路径） / `DELTA-BUG`（增量 bug）

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `SC2-*` | 本 prompt 的「质量门禁」章 |
| 量化评分 | `G2-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 80

**必须通过项（摘要）**：

| ID | 检查项 | 标准 |
|---|---|---|
| `SC2-1` | 公开接口覆盖 | 所有公开 API/函数均已分析 |
| `SC2-2` | 数据流端到端 | 关键数据流可从源头追踪到终点 |
| `SC2-3` | 异常路径枚举 | 每个函数的异常处理路径已列出 |
| `SC2-4` | 缺陷有依据 | 每条 DEF 都引用了具体的代码位置/逻辑 |

> `SC2-4` 尤其重要：**删除无依据的推测**。代码分析最容易出现的
> 质量问题是"发明"代码里不存在的缺陷。

---

## 6. 降级与交接

### 降级路径

代码不完整或无法解析时：标注可分析的范围与盲区，**不得**对未读到的
代码做行为断言。

### 交接

```
P1 ──► P2 ──► P3（领域建模，消费 01/02 的模型信息）
          └─► P4（MBT 设计）
          └─► P5（用例生成，消费全部含 03/04/05）
```

**并行提示**：P2 与 P1 无相互依赖，可并行。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase2_code_analysis_prompt.md`](../../../../skills/testcase-generator/prompts/phase2_code_analysis_prompt.md)
- 增量分析设计：[`../../incremental-code-analysis-design.md`](../../incremental-code-analysis-design.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
