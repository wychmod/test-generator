# Testcase Generator 六阶段流水线

> 目的：把分散在 `prompts/phase0..phase5`、`resources/output_artifacts.md`、`skill.manifest.json` 中的流水线信息，集中描述为一份可被新成员一次读完的「流水线全景图」。
>
> 详细产物协议：[`../../resources/output_artifacts.md`](../../resources/output_artifacts.md)
> 质量门禁细则：[`../quality/quality-gates.md`](../quality/quality-gates.md)
> Skill 入口：[`../../SKILL.md`](../../SKILL.md)
> 能力声明：[`../../skill.manifest.json`](../../skill.manifest.json)

---

## 1. 流水线全景

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  Phase 0           Phase 1           Phase 2           Phase 3             │
│  输入预处理   ──►   需求分析    ──►   代码分析    ──►   领域建模           │
│  (预处理器)         (需求分析师)      (静态分析专家)   (建模专家)            │
│  [质量门 G0]        [质量门 G1]       [质量门 G2]       [质量门 G3]          │
│                                                                            │
│                                                  ┌──────────────────┐     │
│                                                  ▼                  │     │
│                                            Phase 4                  │     │
│                                            MBT 设计                 │     │
│                                            (MBT 架构师)              │     │
│                                            [质量门 G4]                │     │
│                                                  │                  │     │
│  反馈闭环 ◄──────────────────────────────   Phase 5                  │     │
│  (持续改进)                                  用例生成                 │     │
│                                             (用例设计师)              │     │
│                                             [质量门 G5]                │     │
│                                                  │                  │     │
│                                                  ▼                  │     │
│                                          交付物（测试用例集） ◄────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

每个阶段都有三件事：

1. **输入**：上一阶段的产物（必要时加上用户补充输入）。
2. **角色定义 + 能力边界**：在 `prompts/phaseN_*.md` 顶部明示。
3. **输出 + 质量门禁**：必须通过对应阶段的门禁检查才能进入下一阶段。

---

## 2. Phase 0 — 输入预处理（Input Preprocessing）

**对应核心能力**：输入质量预处理

| 维度 | 内容 |
|---|---|
| 角色 | 智能输入处理器 + 数据质量专家 |
| 入口 | 用户原始输入（文件 / 文本 / 代码 / PRD / OpenAPI / 缺陷上下文） |
| 出口 | Phase 1 的规范化输入 + 质量评分 + 阻断项清单 |
| 关键产物 | `00_input_validation_report.md` / `00_normalized_input.md` / `00_enhancement_suggestions.md` / `00_blockers_and_assumptions.md` |
| 触发场景 | 输入格式混杂、文档质量未知、需求模糊、上传长文档 |

**核心职责**：
- 多格式解析（PDF / Markdown / Word / Excel / JSON / YAML / OpenAPI / Gherkin / 源代码）
- 内容质量评估与缺口识别
- 敏感信息自动脱敏
- 阻断项决策（信息不足时降级为「草稿/测试点/风险清单」而非伪造完整用例）
- 假设显式标注（所有非输入直接给出的规则均标 [假设: 依据]）

**降级路径**：
- 阻断项轻微 → 输出"缺口清单 + 测试点清单"轻量交付
- 阻断项中等 → 输出"草稿级需求分析 + 风险摘要"
- 阻断项严重 → 直接停止流水线，要求用户补充输入

详细规则：[`../../prompts/phase0_input_preprocessing_prompt.md`](../../prompts/phase0_input_preprocessing_prompt.md)

---

## 3. Phase 1 — 需求分析（Requirements Preprocessing）

**对应核心能力**：可测试需求抽取、输入质量预处理

| 维度 | 内容 |
|---|---|
| 角色 | 资深需求分析师 + 测试架构师（IEEE 830 / INCOSE 标准实践者） |
| 入口 | Phase 0 规范化输入 |
| 出口 | 结构化需求条目 + 边界条件 + NFR + 用户旅程 |
| 关键产物 | `01_requirements_summary.md` / `02_testable_requirements.md` / `03_boundary_conditions.md` / `04_nfr_and_impact_analysis.md` |
| 触发场景 | 用户提供 PRD / 需求文档 / 用户故事 / 功能描述；需要从业务目标拆解测试范围 |

**核心职责**：
- 把任意格式输入转为结构化、可测试、可追溯的需求规格
- 提取每个 REQ 的验收标准（AC），平均每条 REQ ≥ 2 条 AC
- 推导边界条件（BVA）+ 等价类（EP）+ 异常场景
- 抽取非功能需求（NFR）并转换为可测试断言
- 建立需求依赖图，检测循环依赖
- 生成用户旅程地图（User Journey Map）

**v2.1 增强**：NFR 完整提取 / 需求影响映射 / 依赖深度分析 / 用户旅程地图

**输出质量底线**：
- 每条 AC 必须可二元判定（禁止"适当/合理/良好"等主观词）
- 所有推断内容标 [推断: 理由]
- 矛盾点必须标 [冲突: 描述]，不得静默跳过

详细规则：[`../../prompts/phase1_requirements_prompt.md`](../../prompts/phase1_requirements_prompt.md)

---

## 4. Phase 2 — 代码分析（Code Analysis）

**对应核心能力**：代码与接口契约辅助分析

| 维度 | 内容 |
|---|---|
| 角色 | 高级软件测试架构师 + 静态代码分析专家 |
| 入口 | Phase 1 需求 + 用户提供的源代码 / API 规范 |
| 出口 | 结构分析 + 数据流分析 + 缺陷雷达 + 契约测试推导 |
| 关键产物 | `01_code_structure.md` / `02_data_flow_analysis.md` / `03_defect_radar.md` / `04_concurrency_analysis.md` / `05_contract_test_derivation.md` |
| 触发场景 | 用户提供代码 / 接口实现 / 服务逻辑 / API 定义；需要补足隐藏分支、异常处理、契约风险 |

**五种分析模式**：

| 模式 | 触发条件 | 标注规范 |
|---|---|---|
| `actual_analysis` | 用户提供完整源代码 | 所有结论基于代码引用 |
| `contract_analysis` | 仅 API 规范（OpenAPI/Swagger/GraphQL/Proto） | 所有内部逻辑标 [预期实现] |
| `requirements_only` | 没有代码 | 仅基于需求推演，标 [逻辑推导] |
| `incremental_analysis` | 有 base/head、diff、PRD/REQ 或上一轮产物 | 结论必须追溯到增量代码行、PRD 匹配和影响面规则 |
| `incremental_hybrid_analysis` | 只有部分 diff、PRD 或历史上下文 | 能增量的部分按增量分析，缺上下文部分标 [增量受限] |

**v2.1 增强**：并发与竞态条件检测 / API 契约测试推导 / 技术债务识别 / 接口兼容性分析

**关键产出**：
- **缺陷雷达**：每条 DEF 必须有代码位置引用（CWE 编号准确），禁止"可能存在…但无法确认"模糊措辞
- **数据流**：DFD Level-0 + 关键数据对象字典 + CFG 关键路径
- **需求-代码映射**：≥ 90% REQ 关联到代码位置
- **增量代码行扫描**：`00_incremental_scope.md` 记录 changed lines、PRD 符合性和新增潜在 bug 信号

详细规则：[`../../prompts/phase2_code_analysis_prompt.md`](../../prompts/phase2_code_analysis_prompt.md)

---

## 5. Phase 3 — 领域建模（Domain Modeling）

**对应核心能力**：领域模型与状态模型构建

| 维度 | 内容 |
|---|---|
| 角色 | 业务领域建模专家 + 测试数据架构师（DDD / 状态机理论 / 组合测试） |
| 入口 | Phase 1 需求 + Phase 2 代码分析 |
| 出口 | 业务实体模型 + 状态机规格 + 参数空间 |
| 关键产物 | `01_business_domain_model.md` / `02_state_machine_spec.md` / `03_test_parameter_space.md` / `04_event_storming_model.md` / `05_temporal_constraints.md` |
| 触发场景 | 存在状态流转、复杂规则、角色权限、生命周期管理；需要为 MBT 建立稳定抽象模型 |

**核心产出**：
- **ERD**：核心实体（Core / Associated / Value Object / Event / Enum）
- **状态机**：Mealy / Moore / Statechart 任选其一，必须满足入边/出边完备性、无孤立/不可达状态、守卫互斥完备
- **参数空间**：所有影响测试结果的输入变量 + 取值范围 + 依赖关系 + 特殊值（Null/Empty/SpecialChar/Unicode/Overflow）
- **事件风暴**（v2.1）：关键事件、命令、聚合、边界上下文
- **时序约束**（v2.1）：超时、顺序依赖、集成点

**重要约束**：
- 总状态数 < 50（或已应用优化策略）
- 无死状态
- 与 Phase 1/2 术语全局统一

详细规则：[`../../prompts/phase3_domain_analysis_prompt.md`](../../prompts/phase3_domain_analysis_prompt.md)

---

## 6. Phase 4 — MBT 设计（Model-Based Testing Design）

**对应核心能力**：MBT 导向测试设计

| 维度 | 内容 |
|---|---|
| 角色 | MBT 架构师 + 测试设计专家（ISTQB Advanced Level） |
| 入口 | Phase 1-3 全部产物 |
| 出口 | 测试模型规格 + 状态转换图 + 覆盖准则 + 路径优化策略 |
| 关键产物 | `01_test_model_specification.md` / `02_state_transition_graph.md` / `03_coverage_criteria.md` / `04_mutation_testing_strategy.md` / `05_error_guessing_checklist.md` |
| 触发场景 | 用户需要基于模型生成测试；系统状态复杂，单靠手工列举容易漏测 |

**业务模型 → 测试模型**：

| 业务模型 | 测试模型 | 转换规则 |
|---|---|---|
| 实体 `ENT-NNN` | 测试对象 `TO-NNN` | 每个独立测试实体映射 |
| 属性 | 测试变量 `TV-NNN` | 影响测试结果的属性 |
| 状态 `S-NNN` | 测试状态 `TS-NNN` | 直接映射，可合并等价状态 |
| 转换 `T-NNN` | 测试步骤 `TTSTEP-NNN` | 每个可测试转换 |
| 守卫条件 `G-NNN` | 测试前置 `TPRE-NNN` | 映射为测试前置 |
| 动作 `Action` | 验证点 `TVERIF-NNN` | 动作结果成为验证点 |

**v2.1 增强**：变异测试策略 / 错误猜测法集成 / 探索性测试空间 / 覆盖率优化算法（遗传算法/模拟退火）

**覆盖准则分层**：
- **Smoke**：冒烟测试路径，关键状态快速验证
- **Critical**：Critical/High 风险路径
- **Standard**：常规路径 + 状态覆盖
- **Full**：全路径 + 转换覆盖 + 边界 + 异常

**优化目标**：
- MTS 大小 ≤ 全路径数 × 0.5
- 单点覆盖元素占比 < 30%
- 状态爆炸控制（< 50 个状态）

详细规则：[`../../prompts/phase4_mbt_design_prompt.md`](../../prompts/phase4_mbt_design_prompt.md)

---

## 7. Phase 5 — 用例生成（Test Case Generation）

**对应核心能力**：结构化测试用例生成、追溯矩阵与质量门禁

| 维度 | 内容 |
|---|---|
| 角色 | 测试用例设计专家 + 测试自动化架构师 |
| 入口 | Phase 1-4 全部产物 |
| 出口 | 测试用例集 + 测试套件摘要 + 追溯矩阵 + 混沌场景 + 数据工厂 |
| 关键产物 | `01_testcase_collection.md` / `02_test_suite_summary.md` / `03_traceability_matrix.md` / `04_test_data_strategy.md` / `05_resilience_and_chaos_cases.md` |
| 触发场景 | 需要正式测试用例交付物 / 回归测试集 / 接口测试集 / 完整追溯矩阵 |

**用例 ID 规范**：

```
TC-{PHASE}-{MODULE}-{SEQUENCE:03d}

PHASE    = 功能域缩写（AUTH / ORDER / PAY / USER 等）
MODULE   = 子模块缩写（LOGIN / REGO / CART / CHECKOUT）
SEQUENCE = 三位数字序号（001 / 002 / ...）

示例:
  TC-AUTH-LOGIN-001    认证模块-登录功能-第1条
  TC-ORDER-CART-015    订单模块-购物车-第15条
```

**用例分类目标占比**：

| 类别 | 占比目标 |
|---|---|
| 正向功能 | ~40% |
| 边界条件 | ~20% |
| 异常处理 | ~20% |
| 安全性 | ~10% |
| 性能 / 兼容 | ~10% |

**v2.1 增强**：混沌工程场景 / 测试数据工厂模式 / 多维度优先级排序 / 执行依赖图与拓扑排序

**输出质量底线**：
- 每个标题唯一且描述测试目标
- 前置条件充分（无隐式假设）
- 步骤可执行（自动化或手工指令可转换）
- 输入数据明确（具体值或来源）
- 预期结果二元化（Pass/Fail 可判定）
- 后置状态可验证

详细规则：[`../../prompts/phase5_testcase_generation_prompt.md`](../../prompts/phase5_testcase_generation_prompt.md)

---

## 8. 三种交付深度

不是所有任务都要走完六个阶段。根据用户场景选择深度：

### 8.1 轻量交付（Light）

**适用**：快速讨论 / 需求评审前期 / 只要测试点或补充清单

**输出**：测试点清单 + 边界条件列表 + 风险与缺口摘要

**跳过**：Phase 3 / 4 / 5 的大部分产物

### 8.2 标准交付（Standard）

**适用**：常规功能模块 / Sprint 级测试设计 / API / 页面 / 业务流程测试

**输出**：可测试需求清单 + 结构化测试用例 + 边界+异常+回归场景 + 简版追溯关系

**保留**：Phase 0 / 1 / 5 全部，Phase 2 / 3 / 4 简版

### 8.3 完整交付（Full）

**适用**：高风险流程 / 复杂状态流转 / 金融、支付、审批、订单、合规类系统

**输出**：分阶段分析产物 + 领域/状态模型 + MBT 设计结果 + 全量测试用例 + 追溯矩阵 + 质量总结

**保留**：所有阶段全部完整产物

---

## 9. 反馈闭环

Skill 在交付后支持基于反馈的迭代改进：

- 用户提供**执行结果** → 反向补强边界与异常场景
- 用户提供**漏测场景** → 扩展参数空间或状态机
- 用户提供**规则修正** → 更新 prompt 或 manifest 中的能力声明

反馈入口由 [`../../resources/feedback_template.md`](../../resources/feedback_template.md) 提供。

---

## 10. 流水线与 skill.manifest.json 的对应关系

`skill.manifest.json` 中声明的 7 项核心能力，按阶段承接如下：

| 核心能力 | 主要承接阶段 |
|---|---|
| 输入质量预处理 | Phase 0 |
| 可测试需求抽取 | Phase 1 |
| 代码与接口契约辅助分析 | Phase 2 |
| 领域模型与状态模型构建 | Phase 3 |
| MBT 导向测试设计 | Phase 4 |
| 结构化测试用例生成 | Phase 5 |
| 追溯矩阵与质量门禁 | Phase 5 + 全局 |

**审计保障**：每次打包前 `devtools/capability_audit.py` 会校验 7 项核心能力是否仍可被入口或资源文件发现。任何阶段 prompt 的删除/重命名都会被审计捕获。
