# 产物契约字典

> 本文件是 [`README.md`](README.md) 所述的 agent 划分参考的一部分。
> **参考架构，不入包。**
>
> **权威来源**：`skills/testcase-generator/resources/output_artifacts.md`。
> 本表与其**逐字一致**；改一边必须同步另一边（`.harness/eval/run_eval.py`
> 的 `product_contract` 检查守卫两者的一致性）。

---

## 为什么要这份字典

在多 agent 系统里，agent 之间**只能靠产物名交接**。产物名一旦不一致，
会出现"上游产出了文件、下游去找另一个名字"，且**不会报错**——
下游只是找不到，然后重新生成一份，造成重复劳动与真相分裂。

本字典是让交接**可机械校验**的单一来源。

---

## 1. 产物总表（权威清单）

### Phase 0 — 输入预处理

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `00_input_validation_report.md` | 输入质量评估、格式识别、主要风险 | **总是** | 全局参考 + 编排者路由 |
| `00_normalized_input.md` | 规范化后的正文内容与结构整理 | **总是** | P1（正式输入） |
| `00_enhancement_suggestions.md` | 补充信息建议、歧义点、缺失项 | 存在缺口时 | 用户 |
| `00_blockers_and_assumptions.md` | 阻断项、强假设项、继续生成的前提条件 | 存在阻断/假设时 | 编排者降级判定 |

### Phase 1 — 需求分析

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `01_requirements_summary.md` | 需求摘要、功能分解、测试目标 | **总是** | 全局参考 |
| `02_testable_requirements.md` | 可测试需求条目化清单（含 AC） | ≥ 1 条 REQ | P4（模型变量来源）、P5 |
| `03_boundary_conditions.md` | 边界条件、等价类、异常情况 | ≥ 1 个参数分析 | P4、P5 |
| `04_nfr_and_impact_analysis.md` | 非功能需求、影响分析、关键用户旅程 | 输入含 NFR 或存在跨模块影响 | P5 |

### Phase 2 — 代码分析

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `00_incremental_scope.md` | 增量代码行扫描、PRD 符合性、潜在 bug 信号 | 增量模式适用 | P5 |
| `01_code_structure.md` | 模块结构、调用关系、主要职责 | **总是** | P3、P4 |
| `02_data_flow_analysis.md` | 数据流、控制流、关键依赖 | **总是** | P3、P4 |
| `03_defect_radar.md` | 潜在缺陷点、脆弱逻辑、风险判断（含技术债务） | **总是** | P5 |
| `04_concurrency_analysis.md` | 并发、竞态、锁或异步风险 | 存在并发场景 | P5 |
| `05_contract_test_derivation.md` | 接口契约测试推导 | 有 API 定义 | P5 |

### Phase 3 — 领域建模

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `01_business_domain_model.md` | 业务实体、关系与职责 | **总是** | P4 |
| `02_state_machine_spec.md` | 状态、事件、转换条件、非法路径 | **总是** | P4（核心输入） |
| `03_test_parameter_space.md` | 参数空间与约束定义 | **总是** | P4 |
| `04_event_storming_model.md` | 关键事件、命令、聚合与边界上下文 | 存在领域事件 | P4、P5 |
| `05_temporal_constraints.md` | 时序约束、超时、顺序依赖、集成点 | 存在时序/集成依赖 | P4、P5 |

### Phase 4 — MBT 设计

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `01_test_model_specification.md` | 测试模型结构与定义 | **总是** | P5 |
| `02_state_transition_graph.md` | 状态转换图或 Mermaid 图 | **总是** | P5 |
| `03_coverage_criteria.md` | 覆盖准则、优先级策略、最小覆盖集 | **总是** | P5 |
| `04_mutation_testing_strategy.md` | 变异测试策略 | 需要评估用例有效性 | P5 |
| `05_error_guessing_checklist.md` | 错误猜测法检查清单 | 需要补充经验性场景 | P5 |

### Phase 5 — 用例生成

| 产物名 | 内容 | 产出条件 | 消费方 |
|---|---|---|---|
| `01_testcase_collection.md` | 完整测试用例集合 | **总是** | 最终交付 |
| `02_test_suite_summary.md` | 规模、覆盖、优先级与风险摘要 | **总是** | 最终交付 |
| `03_traceability_matrix.md` | 需求、模型、场景、用例之间的映射 | **总是** | 最终交付 |
| `04_chaos_engineering_scenarios.md` | 混沌工程场景、故障注入、韧性验证 | 高可用要求系统 | 最终交付 |
| `05_test_data_strategy.md` | 测试数据工厂、样例数据、清洗策略 | 需要可复用测试数据 | 最终交付 |

### 全局产物

| 产物名 | 内容 | 产出者 | 消费方 |
|---|---|---|---|
| `quality_report.md` | 全流水线质量评分汇总 | **编排者**（非阶段 agent） | 交付放行判定 |

---

## 2. 编号规则

```
<SS>_<slug>.md

SS   = 阶段内产物序号（00 给输入侧，01+ 给增量产物）
slug = 英文小写 + 下划线
```

**为什么 04/05 位是"增强位"**：每个阶段的**原生产物**占 `01`-`03`，
v2.1 引入的增强能力占 `04`-`05`。这个规律在六个阶段一致：

| 阶段 | 原生位 | 增强位（v2.1） |
|---|---|---|
| P1 | 01, 02, 03 | 04 |
| P2 | 01, 02, 03 | 04, 05 |
| P3 | 01, 02, 03 | 04, 05 |
| P4 | 01, 02, 03 | 04, 05 |
| P5 | 01, 02, 03 | 04, 05 |

> **编号与启用顺序无关。** 例如 P5 即使只启用"测试数据工厂"而不启用
> "混沌工程"，数据工厂仍占 `05` 位。固定编号让交接契约稳定，
> 不因可选能力的开关而漂移。

---

## 3. ID 命名空间 —— 跨 agent 的追溯载体

产物靠**文件名**交接，内容靠**ID**追溯。ID 命名空间按阶段划分：

| 阶段 | ID 前缀 | 含义 |
|---|---|---|
| P1 | `REQ` / `AC` / `BR` / `EQ` / `PARAM` | 需求 / 验收标准 / 业务规则 / 等价类 / 参数 |
| P2 | `DEF` / `DF` / `FUNC` / `PATH` / `DELTA-BUG` | 缺陷 / 数据流 / 函数 / 路径 / 增量 bug |
| P3 | `ENT` / `S` / `T` / `G` / `INV` / `CMD` / `EVT` / `RM` / `UJM` | 实体 / 状态 / 转换 / 守卫 / 不变式 / 命令 / 事件 / 关系 / 用户旅程 |
| P4 | `TO` / `TS` / `TT` / `PATH` / `MTS` | 测试对象 / 测试状态 / 转换 / 路径 / 变异策略 |
| P5 | `TC` | 测试用例 |

**硬规则**：ID 在跨 agent 传递时**不得重新编号**。
`TC-ORDER-CART-015` 追溯到 `REQ-ORDER-007` 这条链，
就是 `03_traceability_matrix.md` 的全部价值所在。

---

## 4. 文件头元数据契约

每个产物文件的 frontmatter **必须**包含：

```yaml
---
generated_by: testcase-generator v2.3.0
phase: <0-5>
timestamp: {ISO8601}
status: draft / reviewed
quality_score: {0-100}      # 编排者门禁判定依据
version: 1.0
---
```

各阶段附加字段（如 P1 的 `total_requirements`、P2 的 `defects_found`）
见对应 `skills/testcase-generator/prompts/phase*.md` 的「输出规范」章。

> **`quality_score` 是编排者的唯一判据来源。** 若该字段缺失，
> 编排者应视为门禁不通过——没有分数就无法判定放行。

---

## 5. 校验方式

本字典与权威声明的一致性由代码守卫：

```bash
python .harness/eval/run_eval.py
```

其中的 `product_contract` 检查会双向比对：
`output_artifacts.md` 声明的产物名必须被 ≥ 1 个 phase prompt 认领，
且 phase prompt 认领的产物名必须已在 `output_artifacts.md` 中声明。

> 该检查来自两次真实事故：Phase 0 的 `00_input_analysis.md` 是
> 只在 prompt 里出现的"反向孤儿"，而 Phase 5 的 `04`/`05` 编号
> 在声明侧与生产侧被写反。两者都不会报错，只会静默断链。

---

## 6. 相关文件

- 权威声明：[`../../../skills/testcase-generator/resources/output_artifacts.md`](../../../skills/testcase-generator/resources/output_artifacts.md)
- 交付协议：[`../../../skills/testcase-generator/references/delivery-protocol.md`](../../../skills/testcase-generator/references/delivery-protocol.md)
- 编排逻辑：[`orchestration.md`](orchestration.md)
