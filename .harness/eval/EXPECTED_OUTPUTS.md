# EXPECTED_OUTPUTS — 期望产物规范

本表给出 `testcase-generator` 在每个 `test-fixtures/skill-eval/` 样
本上**应当**产出的文件。期望路径以 `test-output/` 为根目录的相对
路径（POSIX 风格），与实际 `test-output/` 目录结构一致。

> 修改本表前请同步更新 `.harness/eval/run_eval.py` 的
> `build_fixture_registry()`，否则 eval 流水线会与本表分叉。

## 全局阈值

| 阶段 | 期望 | 阈值来源 |
|---|---|---|
| **Phase 0 输入预处理** | 输入质量评分 ≥ **80 分**（满分 100） | `README.md` 「质量门禁」表 / `.harness/AGENTS.md` §3 |
| Phase 0 降级路径 | 模糊输入必须先输出「风险摘要 + 缺失信息清单」 | `SKILL.md` §「质量门禁」末段 |
| Phase 5 | 正式用例的字段完整度评分 ≥ 90 | `devtools/skill_quality_audit.py` 中 `FORMAL_SCORE_THRESHOLD` |

## fixture 期望产物

### 1. `login_prd.md` — 登录模块 PRD

- **输入类型**：Markdown PRD / 需求文档
- **覆盖模式**：需求驱动模式（标准交付）
- **能力声明**（应在 SKILL.md + manifest + README 都能找到）：
  - "根据需求或 PRD 生成测试用例"
  - "需求驱动模式"
- **期望产物**：

  | 路径 | 含义 |
  |---|---|
  | `phase1/01_requirements_summary.md` | 需求摘要（结构化） |
  | `phase5/01_testcase_collection.md` | 测试用例集（正式） |

  **隐含期望**：
  - 正向、负向、边界值三类用例齐全
  - 包含账号锁定 5 次 / 30 分钟的安全场景
  - 包含追溯矩阵（每个用例关联 `REQ-LOGIN-*`）

### 2. `order_openapi.yaml` — Order API 规范

- **输入类型**：OpenAPI 3.0 规范
- **覆盖模式**：代码辅助模式（API/契约测试）
- **能力声明**：
  - "根据 API 规范生成接口测试场景"
  - "代码与接口契约辅助分析"
- **期望产物**：

  | 路径 | 含义 |
  |---|---|
  | `phase2/05_contract_test_derivation.md` | 契约测试推导（字段、Schema、错误码矩阵） |
  | `phase5/01_testcase_collection.md` | 测试用例集（API 格式） |

  **隐含期望**：
  - 覆盖 201 / 400 / 401 / 409 四个状态码
  - 包含 `sku` / `quantity` / `addressId` 必填校验
  - 包含 `bearerAuth` 鉴权缺失场景

### 3. `bugfix_regression.py` — 缺陷修复上下文

- **输入类型**：Python 源码 + 缺陷修复说明
- **覆盖模式**：回归聚焦模式 + 代码辅助模式
- **能力声明**：
  - "根据源代码或补丁上下文补充测试路径"
  - "回归聚焦模式"
- **期望产物**：

  | 路径 | 含义 |
  |---|---|
  | `phase2/04_concurrency_analysis.md` | 并发 / 数据竞争分析（优惠券边界） |
  | `phase5/01_testcase_collection.md` | 回归测试用例集（聚焦过期券 + min_spend 边界） |

  **隐含期望**：
  - `BUGFIX_NOTE` 中两条需求（`REQ-COUPON-001` / `-002`）各至少一个
    用例
  - 必须有 `order_total == min_spend` 的边界用例
  - 必须显式标注"过期券不可减免"为安全断言

### 4. `ambiguous_requirement.md` — 模糊需求

- **输入类型**：自然语言需求（缺关键信息）
- **覆盖模式**：降级路径（**禁止**直接出正式测试用例）
- **能力声明**：
  - "输入质量预处理"
  - "歧义与风险识别"
- **期望产物**：

  | 路径 | 含义 |
  |---|---|
  | `phase0/00_input_validation_report.md` | 输入验证报告（缺口、风险、模糊点） |
  | `phase0/00_enhancement_suggestions.md` | 增强建议（让用户补齐信息） |

  **隐含期望**：
  - 必须显式包含「风险摘要」「缺失信息清单」「降级」三类小节
  - 所有推断必须以"假设"标记
  - 如果用户后续补齐信息，可继续 Phase 1+

### 5. `order_lifecycle.md` — 订单状态机

- **输入类型**：状态机 / 业务流程描述
- **覆盖模式**：MBT 导向模式
- **能力声明**：
  - "MBT 导向测试设计"
  - "领域模型与状态模型构建"
- **期望产物**：

  | 路径 | 含义 |
  |---|---|
  | `phase3/04_event_storming_model.md` | Event Storming / 状态模型 |
  | `phase4/04_mutation_testing_strategy.md` | 变异测试 + 覆盖准则（最小路径集） |

  **隐含期望**：
  - 7 个状态全部进入状态机定义
  - 至少 1 条非法路径（"Completed 不允许取消" / "Cancelled 不允
    许支付"）
  - 覆盖准则至少包含「全状态对覆盖 + 全转换覆盖」之一

## 路径风格约定

- 一律使用 POSIX 风格（`phase1/01_*.md`），不要使用 Windows 反斜杠。
- 编号规则：`phase<N>/<SS>_<slug>.md`——`<N>` 是 0-5 的阶段号，
  `<SS>` 是该阶段内的产物序号（`00` 给输入侧、`01+` 给增量产物）。
- 文件名 slug 用英文小写 + 下划线；中文标题放在文件内容 frontmatter
  的 `title` 字段。

## 更新流程

1. 在 `run_eval.py` 的 `build_fixture_registry()` 里改对应 fixture
   的 `expected_outputs`。
2. 在本表对应 fixture 的「期望产物」表格里改路径。
3. 跑 `python .harness/eval/run_eval.py` 验证 eval 与本表一致。
4. 在 `baselines/README.md` 里说明这次改动影响了哪些基线。
