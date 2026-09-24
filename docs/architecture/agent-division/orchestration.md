# 编排者（Orchestrator）契约

> 本文件是 [`README.md`](README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**

编排者**不是**第七个阶段 agent，它不产出任何业务产物。
它只做四件事：**路由、门禁判定、回退、汇总**。

---

## 1. 职责

| 职责 | 说明 | 不做什么 |
|---|---|---|
| **路由** | 根据输入形态决定执行哪几个阶段、以什么顺序 | 不修改任何阶段的产物内容 |
| **门禁判定** | 读取各阶段自评分，与阈值比对，决定放行/重做/降级 | 不替阶段 agent 打分 |
| **回退** | 当上游产物不满足下游输入要求时，决定回退到哪个阶段 | 不绕过门禁硬推 |
| **汇总** | 收集全部产物，触发最终质量报告 | 不重新生成产物 |

> **编排者必须是无状态的。** 它的全部决策依据来自"产物是否存在 + 产物自评分 +
> 输入的形态特征"，而不是会话记忆。这让编排逻辑可重放、可测试。

---

## 2. 路由决策表

编排者在入口处**唯一一次**做出路径决策。判据来自 P0 的产物
（`00_input_validation_report.md` 的「路由决策」段）：

| 输入特征 | 推荐模式 | 执行路径 | 跳过的阶段 |
|---|---|---|---|
| 仅 PRD / 需求文档 / 用户故事 | 需求驱动 | P0 → P1 → P5 | P2, P3, P4 |
| 仅 API 规范（OpenAPI / 接口定义） | 代码辅助 | P0 → P2 → P5 | P1, P3, P4 |
| 源代码 + 缺陷修复说明 | 回归聚焦 | P0 → P2 → P5 | P1, P3, P4 |
| 状态机 / 生命周期 / 复杂业务规则 | MBT 导向 | P0 → P1 → P3 → P4 → P5 | P2 |
| 高风险完整流程（金融 / 支付 / 审批） | 完整流水线 | P0 → P1 → P2 → P3 → P4 → P5 | 无 |
| 需求与代码同时提供 | 混合 | P0 → P1 ∥ P2 → P5（可选 P3/P4） | 按复杂度决定 |

**判定规则**：

1. **P0 永远执行。** 它是唯一不可跳过的阶段——即使输入看起来完整，
   也需要质量评估来决定后续深度。
2. **P5 是终端。** 所有路径都以 P5（或降级交付）结束。
3. **P3/P4 只在需要模型推理时启用。** 判据：是否存在状态流转、
   复杂规则组合、或参数空间爆炸。简单的 CRUD 需求不需要 MBT。
4. **并行只在无依赖时启用。** P1 与 P2 互不依赖，可并行；
   P3 依赖 P1 或 P2 的产出，不可与它们并行。

---

## 3. 门禁判定

编排者在每个阶段提交后执行：

```
读取该阶段产物文件头的 quality_score 字段
  ├─ score >= 阶段阈值          → 放行，把产物交给下游
  ├─ score < 阈值 但 >= 60      → 要求该阶段 agent 补强一次
  │                               （最多重试 1 次，避免打转）
  └─ score < 60 或有阻断项       → 走降级路径：交付风险摘要 + 缺失信息清单
```

阈值表见 [`README.md`](README.md) 第 4 节。

### 3.1 输入不足时的返回顺序（硬规则）

当门禁判定为降级时，**必须**按此顺序返回，不得打乱：

1. **风险摘要** —— 现在有什么风险
2. **缺失信息清单** —— 需要用户补什么
3. **降级版草稿** —— 如果仍有价值才给

> 严禁在信息不足时伪造完整产物。这条规则来源：
> `skills/testcase-generator/references/quality-review.md` §2。

---

## 4. 回退决策

下游发现上游产物不足时，**不自行补救**，而是向编排者请求回退：

| 症状 | 回退目标 | 说明 |
|---|---|---|
| P5 发现需求覆盖不全 | → P1 | 缺失的需求条目应回到需求分析阶段补 |
| P4 发现模型无法覆盖状态 | → P3 | 状态模型不完整，需重建领域模型 |
| P3 发现需求条目不可测试 | → P1 | 需求缺少可判定的验收标准 |
| P5 发现契约测试缺失 | → P2 | 需要补接口契约推导 |
| 任意阶段发现输入质量差 | → P0 | 回到输入预处理重新评估 |

**回退上限**：同一阶段最多回退一次。二次失败即降级交付，
避免无限循环消耗。

---

## 5. 汇总与收尾

全部阶段完成后，编排者：

1. 核对 [`product-contracts.md`](product-contracts.md) 中登记的产物是否齐全
2. 触发 [`review-agent.md`](review-agent.md) 做交付前评审
3. 汇总生成 `quality_report.md`（模板见
   `docs/quality/quality-gates.md` §5）

> **`quality_report.md` 是唯一的全局产物**，横跨全部阶段。
> 它由编排者而非任何阶段 agent 产出——因为它是"跨阶段视角"的产物，
> 让某个阶段 agent 来写会天然偏向自己那一环。

---

## 6. 最小实现骨架

```
orchestrator(input):
    report = run(p0, input)                    # 永远执行
    if report.has_blockers:
        return degrade(report)                 # 风险摘要 + 缺失清单

    path = route(report)                       # 见第 2 节路由表
    artifacts = { p0: report.artifacts }

    for stage in path[1:]:                     # 跳过 p0
        result = run(stage, artifacts)
        if not gate_pass(stage, result):       # 见第 3 节
            if retry_once(stage): continue
            return degrade(result)
        artifacts[stage] = result.artifacts

    review = run(review_agent, artifacts)
    return finalize(review, artifacts)         # 含 quality_report.md
```

---

## 7. 相关文件

- Agent 拓扑总览：[`README.md`](README.md)
- 产物契约字典：[`product-contracts.md`](product-contracts.md)
- 评审 agent：[`review-agent.md`](review-agent.md)
- 各阶段契约：[`agents/`](agents/)
