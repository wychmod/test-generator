# Agent 划分参考 — 把六阶段流水线拆成多 Agent 系统

> **本模块定位：参考架构，不入包。**
> 它不参与 `.skill` / `.zip` / npm 分发（`docs/**` 已在 `skill.manifest.json` 的「分发排除」中），
> 也不被任何审计脚本作为运行时契约扫描。
>
> **读者**：想参照本项目划分"生成测试用例的 agent"以及其提示词的架构设计者。
>
> **读法**：本模块只描述**契约**（职责 / 输入 / 输出 / 门禁 / 降级 / 交接），
> 方法论一律**指针式**引用 `skills/testcase-generator/prompts/`，**不复制正文**。

---

## 1. 这个模块解决什么问题

`testcase-generator` 的运行时提示词已经是一套完整的六阶段流水线，但它被设计成
**在单个 AI 会话内按需加载**：模型读 `SKILL.md` → 按触发时机加载对应 `phase*.md` → 产出该阶段产物。

如果要把这套流程搬到一个**多 Agent 系统**（每个阶段一个 agent、各自持有独立上下文与工具），
真正需要补齐的不是"提示词内容"——那些已经在 `prompts/` 里了——而是三样东西：

| 缺什么 | 为什么必须补 | 本模块的对应物 |
|---|---|---|
| **契约层** | 提示词是写给"一个连续会话"的，不是写给"消息传递的 agent"的。agent 之间只能靠**显式输入输出**交接 | 6 份阶段契约 + 1 份评审契约 |
| **编排层** | 谁先跑、谁可以跳过、哪个阶段失败了要回退 | [`orchestration.md`](orchestration.md) |
| **产物契约字典** | 每个 agent 的产出名必须与上下游一致，否则交接断链 | [`product-contracts.md`](product-contracts.md) |

> **本项目的提示词已经"agent-ready"**。拆分是**抽取**而非重写：
> 每个阶段的 prompt 天然已有 ~7 个同构章节，其中 5 个可 1:1 映射为 agent 定义要素。
> 见下节。

---

## 2. 提示词的同构结构 → Agent 定义要素

六份阶段 prompt 结构高度同构。这个同构性正是"可以机械拆分"的依据：

| prompt 章节 | 映射为 agent 的什么 | 说明 |
|---|---|---|
| 阶段头 banner（版本 / 阶段目标 / 对应核心能力 / 输入来源 → 输出去向） | **入口元数据** | 已经声明了上下游，直接可用 |
| `## 1. 角色定义与能力边界` | **System Prompt** | 核心身份 + ✅能做/⚠️需标注/❌不应做 |
| `## 2. 输入处理协议` | **Input Contract** | 输入类型识别、路由、前置校验 |
| 核心执行步骤（`Step 0..N`） | **Workflow** | 有序步骤，含分支 |
| `## N. 输出规范` | **Output Contract** | 产物文件名 + 文件头元数据 + 模板 |
| 质量门禁（`SC<n>-*` 定性自检 / `G<n>-*` 量化评分） | **Self-check Gate** | 见第 4 节的两套 ID 命名空间 |
| `[v2.1 新增]` 增强章节 | **可选能力开关** | 按输入特征决定是否启用 |

**因此每份 agent 契约只需回答 6 个问题**，不需要重述方法论：

1. **你是谁**（角色，指向 prompt 的 §1）
2. **你收什么**（输入契约，含上游产物名）
3. **你做什么**（执行步骤指针，指向 prompt 的执行章节）
4. **你交什么**（输出契约，含产物名与文件头字段）
5. **你怎么自检**（门禁 ID 与阈值）
6. **什么时候降级 / 交给谁**（降级路径与下游 agent）

---

## 3. Agent 拓扑

### 3.1 最简形态：6 个阶段 agent + 1 个评审 agent

```
                    ┌──────────────────────────┐
                    │  orchestrator（编排者）   │
                    │  路由 / 门禁判定 / 回退    │
                    └────────────┬─────────────┘
                                 │
    ┌──────────┬──────────┬──────┴─────┬──────────┬──────────┐
    ▼          ▼          ▼            ▼          ▼          ▼
 ┌──────┐  ┌──────┐  ┌──────┐    ┌──────┐  ┌──────┐  ┌──────┐
 │  P0  │→ │  P1  │→ │  P2  │ →  │  P3  │→ │  P4  │→ │  P5  │
 │输入   │  │需求   │  │代码   │    │领域   │  │MBT   │  │用例   │
 │预处理 │  │分析   │  │分析   │    │建模   │  │设计   │  │生成   │
 └──────┘  └──────┘  └──────┘    └──────┘  └──────┘  └──────┘
    │          │          │            │         │         │
    └──────────┴──────────┴────────────┴─────────┴─────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  review（独立评审 agent）  │
                    │  交付前必做 6 步核对       │
                    └──────────────────────────┘
```

### 3.2 关键设计原则：P2 是可跳过的旁路，而非必经环节

**这条最容易做错。** 六个阶段**不是**一条强串行链：

| 输入形态 | 实际路径 | 说明 |
|---|---|---|
| 只有 PRD / 需求文档 | P0 → P1 → P5 | **跳过 P2/P3/P4**，需求驱动模式 |
| 只有 API 规范 | P0 → P2 → P5 | 代码辅助模式，P1 可轻量化 |
| 只有源代码 + 缺陷说明 | P0 → P2 → P5 | 回归聚焦模式 |
| 状态机 / 复杂业务规则 | P0 → P1 → P3 → P4 → P5 | MBT 导向模式 |
| 高风险完整流程 | P0 → P1 → P2 → P3 → P4 → P5 | 完整模式 |

> 把 P0-P5 硬编码成"必须依次全部执行"是多 agent 化最常见的误实现：
> 它会让只给了一份 PRD 的用户被迫等待代码分析 agent 空转。
> **编排者必须先做输入识别，再决定路径**——这正是 P0 的职责。

### 3.3 扩展形态

| 形态 | 何时需要 | 做法 |
|---|---|---|
| **评审 agent 独立** | 交付物要对外承诺质量 | 见 [`review-agent.md`](review-agent.md)。**裁判席不在自己辖区里** |
| **P1/P2 并行** | 同时拿到需求与代码 | P1 与 P2 无相互依赖，可并行 |
| **P3/P4 合并** | 模型简单、时序宽松 | 两者都以领域模型为输入，合并可省一次交接 |
| **按模块扇出** | 大型系统多模块 | 对每个模块起一组 P1→P5，最后统一汇总追溯矩阵 |

---

## 4. 两套质量门禁 ID —— 不要混用

这是本仓库一个**刻意的设计**，拆 agent 时必须保留：

| 命名空间 | 位置 | 性质 | 用途 |
|---|---|---|---|
| `G<阶段>-<组>-<序号>` | `skills/testcase-generator/resources/quality_checklist.md` | **量化**，带权重 | 计算阶段得分，决定能否放行 |
| `SC<阶段>-<序号>` | 各 `skills/testcase-generator/prompts/phase*.md` 的「质量门禁」章 | **定性**，无权重 | 模型在提交前的自检清单 |

**为什么分开**：自检清单要能被模型逐条勾选（定性），而放行判定需要可加权求和的分数（量化）。
把两者合成一套 ID，会让"自检"变成"算分"，模型容易为了凑分而自我美化。

各阶段阈值（来源：`README.md` 「质量门禁」表）：

| 阶段 | 阈值 |
|---|---|
| P0 输入预处理 | ≥ 80 |
| P1 需求分析 | ≥ 80 |
| P2 代码分析 | ≥ 80 |
| P3 领域建模 | ≥ 85 |
| P4 MBT 设计 | ≥ 85 |
| P5 用例生成 | ≥ 90 |

> P5 的 90 分对应 `devtools/skill_quality_audit.py` 的 `FORMAL_SCORE_THRESHOLD`——
> 只有达到它，产物才可声明为"正式测试用例"。低于阈值只能交付草稿。

---

## 5. 模块导航

| 文件 | 回答什么问题 |
|---|---|
| [`orchestration.md`](orchestration.md) | 谁先跑、路径怎么选、失败了回退到哪 |
| [`product-contracts.md`](product-contracts.md) | 每个 agent 的产物名是什么、被谁消费 |
| [`agents/p0-input-preprocessing.md`](agents/p0-input-preprocessing.md) | P0 agent 契约 |
| [`agents/p1-requirements.md`](agents/p1-requirements.md) | P1 agent 契约 |
| [`agents/p2-code-analysis.md`](agents/p2-code-analysis.md) | P2 agent 契约 |
| [`agents/p3-domain-modeling.md`](agents/p3-domain-modeling.md) | P3 agent 契约 |
| [`agents/p4-mbt-design.md`](agents/p4-mbt-design.md) | P4 agent 契约 |
| [`agents/p5-testcase-generation.md`](agents/p5-testcase-generation.md) | P5 agent 契约 |
| [`review-agent.md`](review-agent.md) | 评审 agent 契约（独立裁判） |

---

## 6. 使用这份参考时的注意事项

1. **产物名是硬契约。** 本模块 `product-contracts.md` 中的产物名与
   `skills/testcase-generator/resources/output_artifacts.md` **逐字一致**。
   改一边必须改另一边，否则交接断链。
2. **不要在 agent 契约里复制方法论正文。** 契约只写"做什么、交什么"，
   "怎么做"始终指向 `skills/testcase-generator/prompts/phase*.md`。复制会造成两份真相。
3. **ID 命名空间要贯通。** `REQ-*` / `DEF-*` / `ENT-*` / `TO-*` / `TC-*` 是
   agent 之间追溯关系的载体，跨 agent 传递时不能重新编号。
4. **降级路径必须显式。** 输入不足时 agent 应当返回"风险摘要 + 缺失信息清单"，
   而不是伪造完整产物。这条规则在全部阶段生效（见 `skills/testcase-generator/references/quality-review.md`）。

---

## 7. 相关文件

- 六阶段流水线详解：[`../pipeline-overview.md`](../pipeline-overview.md)
- 产物权威声明：[`../../../skills/testcase-generator/resources/output_artifacts.md`](../../../skills/testcase-generator/resources/output_artifacts.md)
- 量化质量门禁：[`../../../skills/testcase-generator/resources/quality_checklist.md`](../../../skills/testcase-generator/resources/quality_checklist.md)
- 交付协议：[`../../../skills/testcase-generator/references/delivery-protocol.md`](../../../skills/testcase-generator/references/delivery-protocol.md)
- 质量评审动作：[`../../../skills/testcase-generator/references/quality-review.md`](../../../skills/testcase-generator/references/quality-review.md)
