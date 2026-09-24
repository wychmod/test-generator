# 评审 Agent 契约 — 独立交付评审

> 本文件是 [`README.md`](README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **方法论指针**：`skills/testcase-generator/references/quality-review.md`

---

## 1. 身份

| 项 | 值 |
|---|---|
| 名称 | `quality-review` |
| 角色 | 独立质量评审（第三方视角） |
| 对应能力 | 追溯矩阵与质量门禁 |
| 可跳过 | 否（声明"正式测试用例"前必经） |

### 核心设计原则：裁判席不在自己辖区里

评审 agent **必须**独立于 P1-P5 的生产链：

- **不共享上下文**：评审者只看产物，不看生产过程中的自我说明。
  生产 agent 的"我已经覆盖了"不能作为证据。
- **不修改产物**：评审者只报告问题，修复由对应阶段 agent 负责。
  自己修自己审等于没有审。
- **有否决权**：评审不通过 → 不允许声明"正式测试用例"。

> 这是本仓库反复出现的根因设计原则。`.harness/reins/auditor/AGENT.md`
> 的"只报告问题、把问题派给对应 reins"与本契约同构。

---

## 2. 输入契约

| 输入 | 说明 |
|---|---|
| 全部阶段产物 | 按 [`product-contracts.md`](product-contracts.md) 的清单核对齐全性 |
| 各阶段自评分 | 产物文件头的 `quality_score` 字段 |
| 交付深度声明 | 轻量 / 标准 / 完整 |

---

## 3. 执行流程

交付结构化测试用例前**至少**完成以下 6 步（来源：`skills/testcase-generator/references/quality-review.md` §1）：

| # | 检查 |
|---|---|
| 1 | 高风险需求是否被优先覆盖 |
| 2 | 每条用例是否具备可执行步骤与可验证预期结果 |
| 3 | 是否存在明显重复或仅换表述的冗余用例 |
| 4 | 边界、负向、权限、状态流转场景是否遗漏 |
| 5 | 所有推断内容是否被明确标记 |
| 6 | 是否存在输入缺陷导致的不可判定项，并在输出中显式保留 |

> 此清单是**交付前的必做动作**，不是可选项。逐条核对后再声明"正式测试用例"。

**能力边界**（评审者必须向用户明示）：

- 本评审通过结构化分析提高测试产出质量，**不能替代人工领域确认**
- 业务规则存在歧义时应**显式保留歧义**，而不是悄悄猜测
- MBT 深度应由**复杂度驱动**，不是默认对所有小需求启用

---

## 4. 输出契约

评审 agent **不产出新的业务产物**，它产出：

| 输出 | 形态 | 说明 |
|---|---|---|
| 评审结论 | `PASS` / `PASS_WITH_WARNINGS` / `FAIL` | 写入 `quality_report.md` 的 `verdict` 字段 |
| 问题清单 | 按阶段归组 | 每条问题指向对应阶段 agent 修复 |
| 降级判定 | 交付级别声明 | 最低交付协议核对结果 |

**最低交付协议**（来源：`skills/testcase-generator/references/delivery-protocol.md`）：

- 结构化测试用例必须包含 10 个必填字段
- 缺失 ≥ 3 个字段 → **不能**声明"正式测试用例"，只能按草稿交付

**与推断有关的硬规则**（全部阶段生效，不可放宽）：

- 不凭空编造需求、业务规则或预期结果；必须推断时明确标记
- 始终保留来源与结论之间的**追溯关系**
- 明确区分"已确认信息"与"推断信息"
- 若代码实现与需求描述冲突，**以代码为当前实现**，同时显式指出需求不一致

---

## 5. 门禁

评审 agent 自身没有量化门禁——它是**执行**门禁判定的一方。
判定依据：

| 判定 | 条件 |
|---|---|
| `PASS` | 全部 6 步通过 + `quality_score` ≥ 90（P5） |
| `PASS_WITH_WARNINGS` | 6 步通过但存在已标注的警告项 |
| `FAIL` | 任一必做步骤不通过，或必填字段缺失 ≥ 3 |

---

## 6. 降级与交接

```
P5 ──► review ──┬─► PASS          → 最终交付（正式测试用例）
                ├─► WITH_WARNINGS → 最终交付（带警告声明）
                └─► FAIL          → 问题派回对应阶段 agent → 重跑该阶段 → 再评审
```

**评审失败不直接终止流水线**：问题按阶段归组后派回生产链，
修复后只需重跑受影响的阶段（编排者按 [`orchestration.md`](orchestration.md)
第 4 节的回退决策处理）。

---

## 7. 相关文件

- 评审动作与边界：[`../../../skills/testcase-generator/references/quality-review.md`](../../../skills/testcase-generator/references/quality-review.md)
- 交付协议：[`../../../skills/testcase-generator/references/delivery-protocol.md`](../../../skills/testcase-generator/references/delivery-protocol.md)
- 编排逻辑：[`orchestration.md`](orchestration.md)
