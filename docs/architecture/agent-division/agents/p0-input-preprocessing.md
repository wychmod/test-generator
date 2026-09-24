# P0 Agent 契约 — 输入预处理

> 本文件是 [`../README.md`](../README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/prompts/phase0_input_preprocessing_prompt.md`
> （本契约不复制正文，只抽取 agent 定义要素）

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `p0-input-preprocessing` |
| 角色 | 智能输入处理器 + 数据质量专家 |
| 对应能力 | 输入质量预处理 |
| 可跳过 | **否** —— 唯一必经阶段 |

**System Prompt 来源**：prompt 的 `## 1. 角色定义与能力边界` 章。

核心边界（摘要）：

- ✅ 识别输入类型并选择处理策略；从各种格式提取有效内容；评估质量与完整性
- ⚠️ 无法解析 → 标注 `[无法解析: 原因]`；需人工确认 → `[需确认]`；敏感信息 → 自动脱敏并标注 `[已脱敏]`
- ❌ 修改用户原始意图；跳过安全检查；把低质量输入静默传递给下游

---

## 2. 输入契约

| 输入 | 形态 |
|---|---|
| 用户原始输入 | 文件（PDF / Word / Markdown / Excel / JSON / YAML / OpenAPI）或纯文本或 URL |
| `[参考知识]` 块 | 可选。知识库检索结果，**不是**用户当前需求本身 |

**前置校验**：

- 有效内容 < 50 字符 → 触发 `E0-004`，列出最小需求信息清单
- 文件 > 10MB 或页数 > 200 → 触发 `E0-005`，建议拆分
- 检测到注入代码 / 恶意内容 → 触发 `E0-007`，隔离并要求用户确认

---

## 3. 执行流程

指向 prompt 的 `## 2. 输入类型识别与路由` 与 `## 3.` 执行章。

**Step 0：知识库上下文识别**（当输入含 `[参考知识]` 块）

- 保留来源标识，格式 `KB: <filename>#<heading>`
- 在 `00_input_validation_report.md` 中记录命中来源与用途
- 在 `00_normalized_input.md` 中单独保留 `[参考知识]` 区块，供 P1/P5 使用
- 知识库**不能覆盖**用户当前需求；冲突时标注 `KB 冲突`，以当前输入为主来源

**后续步骤**：格式识别 → 质量评分 → 安全扫描 → 脱敏 → 规范化 → 路由决策。

---

## 4. 输出契约

| 产物名 | 产出条件 | 消费方 |
|---|---|---|
| `00_input_validation_report.md` | **总是** | 全局参考 + 编排者路由 |
| `00_normalized_input.md` | **总是** | P1 |
| `00_enhancement_suggestions.md` | 存在缺口时 | 用户 |
| `00_blockers_and_assumptions.md` | 存在阻断/假设时 | 编排者降级判定 |

文件头元数据与模板见 prompt 的 `## 5. 输出规范` 章。

**关键输出字段**：`input_quality_score`、`quality_grade`、`security_scan`、`status`
（`ready_for_phase_1` / `needs_attention`），以及「处理决策」中的
推荐流水线模式 / 推荐测试深度 —— **后者是编排者路由的唯一依据**。

---

## 5. 门禁

| 类型 | ID 命名空间 | 位置 |
|---|---|---|
| 定性自检 | `Q0-*` | 本 prompt 的「质量门禁」章 |
| 量化评分 | `G0-*` | `skills/testcase-generator/resources/quality_checklist.md` |

**阈值**：≥ 80

**警告项**：

| ID | 触发条件 | 处理 |
|---|---|---|
| `W0-1` | 质量评分 < 60 分 | 强烈建议补充信息，但仍继续 |
| `W0-2` | 检测到敏感信息 | 已脱敏但需通知用户 |
| `W0-3` | 输入语言混合 | 建立术语表 |
| `W0-4` | 文件较大（> 5MB） | 注意性能影响 |

---

## 6. 降级与交接

### 降级路径

存在阻断项时，**必须**按序返回：

1. 风险摘要
2. 缺失信息清单
3. 降级版草稿（如仍有价值）

> 若阻断项直接影响正式用例的正确性，**不得**跳过说明后直接输出"正式交付物"。

### 交接

```
P0 ──► 编排者（读取路由决策，决定后续路径）
    └─► P1（消费 00_normalized_input.md）
```

**本 agent 是编排者的决策输入源**，不是单纯的"格式转换器"。
它产出的「推荐流水线模式」决定整个系统的后续拓扑。

---

## 7. 相关文件

- 完整方法论：[`../../../../skills/testcase-generator/prompts/phase0_input_preprocessing_prompt.md`](../../../../skills/testcase-generator/prompts/phase0_input_preprocessing_prompt.md)
- 产物契约：[`../product-contracts.md`](../product-contracts.md)
- 编排逻辑：[`../orchestration.md`](../orchestration.md)
