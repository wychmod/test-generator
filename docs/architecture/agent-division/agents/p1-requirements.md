# P1 Agent 契约 — 需求分析

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase1_requirements_prompt.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p1-requirements` |
| 角色 | 资深需求分析师 + 测试架构师（15+ 年经验） |
| 对应能力 | 可测试需求抽取 |
| 可跳过 | 是（仅 API 规范 / 纯代码输入时可跳过） |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

专业面：需求工程全流程、ISO/IEC/IEEE 29119-3:2021 / INCOSE 需求规格标准实践。

---

## 2. 输入契约

| 输入 | 来源 |
|---|---|
| 规范化后的输入正文 | P0 的 `00_normalized_input.md` |
| `[参考知识]` 区块 | 同上（术语、规范、边界候选，仅作参考） |
| 输入验证报告 | P0 的 `00_input_validation_report.md`（用于了解已知缺口） |

---

## 3. 执行流程

指向 prompt 的核心执行章。要点：

- 需求分解树构建
- 从业务目标拆解功能点
- 为每条需求建立可二元判定的验收标准（AC）
- 参数分析（边界值 BVA / 等价类 EP）
- 歧义与冲突检测

**v2.1 增强章节**（按输入特征启用）：

| 章 | 内容 | 写入 |
|---|---|---|
| §8 | 非功能需求 (NFR) 完整提取与可测试化 | `04_nfr_and_impact_analysis.md`（Part A） |
| §9 | 需求影响映射与风险传播分析 | `04_nfr_and_impact_analysis.md`（Part B） |
| §10 | 用户旅程地图 (User Journey Map) | `04_nfr_and_impact_analysis.md`（Part C） |

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `01_requirements_summary.md` | **总是** | 全局参考 |
| `02_testable_requirements.md` | ≥ 1 条 REQ | P4、P5 |
| `03_boundary_conditions.md` | ≥ 1 个参数分析 | P4、P5 |
| `04_nfr_and_impact_analysis.md` | 输入含 NFR 或存在跨模块影响 | P5 |

**ID 命名空间**：`REQ`（需求） / `AC`（验收标准） / `BR`（业务规则） /
`EQ`（等价类） / `PARAM`（参数）

> **这些 ID 是跨 agent 追溯链的起点。** P4 的测试对象与 P5 的用例
> 都会回溯到 `REQ-*`，因此**不得**在后续阶段重新编号。

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `SC1-*` | 本 prompt 的「质量门禁」章 |
| 量化评分 | `G1-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 80

**必须通过项（摘要）**：

| ID | 检查项 | 标准 |
|---|---|---|
| `SC1-1` | 需求完整性 | 所有功能点都已提取，无遗漏 |
| `SC1-2` | 需求可测试性 | 每条 REQ 至少有 1 条可二元判定的 AC |
| `SC1-3` | 边界覆盖完整 | 所有输入/输出参数都有 BVA 和 EP |
| `SC1-4` | 歧义已标注 | 模糊表述均已标记 `[需确认]` 或 `[推断]` |
| `SC1-5` | ID 唯一性 | REQ/AC/BR/EQ/PARAM ID 无重复 |
| `SC1-6` | 术语一致性 | 同一概念全程使用相同术语 |

---

## 6. 降级与交接

### 降级路径

输入信息不足时按序返回：风险摘要 → 缺失信息清单 → 降级版草稿。

需求内部矛盾无法调和时（`E1-003`）：产出冲突报告，**暂停进入下一阶段**，等待用户仲裁。

### 交接

```
P0 ──► P1 ──► P3（领域建模，消费需求条目）
          └─► P4（MBT 设计，消费需求条目 + 边界条件）
          └─► P5（用例生成，消费全部）
```

**并行提示**：P1 与 P2 无相互依赖，同时拿到需求与代码时可并行执行。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase1_requirements_prompt.md`](../../../../skills/testcase-generator/prompts/phase1_requirements_prompt.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
