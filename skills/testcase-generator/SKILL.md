---
name: testcase-generator
version: 2.3.0
description: 从需求文档、PRD、API 规范、源代码、缺陷修复上下文或功能描述中生成结构化、可追溯、可执行的软件测试用例与测试设计产物。当用户提出生成、扩展、评审、标准化、优化或审计测试用例、测试场景、测试点清单、MBT 导向测试设计结果或测试文档时使用。已为 26 个主流 AI 宿主提供完整或软适配入口（宿主清单与各自路径见分发包根目录的 `HOST_COMPATIBILITY.md`，此处不再逐一枚举，以免宿主扩充时本字段滞后）。v2.2.0 起支持可选的本地 `knowledge/` 知识库（术语表 / 项目规范 / 历史用例）的触发式检索，以及通过大模型自动从 PDF / Markdown / TXT / 图片 / 粘贴文本中录入知识条目（详见仓库 `docs/architecture/knowledge-base.md`）。
---

# Testcase Generator

把原始输入逐步转化为**可追溯、可执行、可验证**的测试设计与用例产物，而不是堆砌数量。

本文件只承担**能力声明、触发时机与资源路由**；细则按需读取 [`references/`](references/)，避免把全部内容堆进入口。

## 触发时机

- 生成、扩展、评审、标准化或审计测试用例 / 测试场景 / 测试点清单
- 从 PRD、需求文档、用户故事、功能描述推导测试范围
- 从 API 规范（OpenAPI / Swagger / GraphQL / Proto）推导契约测试
- 从源代码或 diff / patch 补充测试路径与回归建议
- 为状态流转复杂的业务流程做 MBT 导向测试设计

支持输入：需求文档、PRD、用户故事、功能描述、API 规范、源代码、缺陷与回归背景、本地 Markdown / PDF 需求文件。

支持产出：结构化测试用例、测试场景清单、测试点与边界条件清单、需求到用例的追溯矩阵、面向状态流转的测试设计、面向评审的质量检查与缺口说明。

## 核心能力

本 Skill 对外声明的核心能力（与 `skill.manifest.json` 字段对齐）：

- **输入质量预处理**：对需求 / PRD / API / 源代码等输入先做规范化、缺口识别与质量评分。
- **可测试需求抽取**：从原始输入中提取结构化需求、约束与关键业务规则。
- **代码与接口契约辅助分析**：在提供代码或 API 时补充控制流、数据流、异常路径与契约风险。
- **领域模型与状态模型构建**：在存在状态流转或复杂业务规则时建立领域模型与状态机。
- **MBT 导向测试设计**：围绕覆盖准则、风险导向与状态转换路径做模型化测试设计。
- **结构化测试用例生成**：产出可追溯、可执行、可验证的测试用例与场景清单。
- **追溯矩阵与质量门禁**：在需求 ↔ 用例之间建立双向追溯，并按质量门禁校验产物。

## 核心工作流

当任务需要完整分析深度时按顺序执行：

1. 识别输入类型并进行规范化（Phase 0）。
2. 提取可测试需求、约束和关键业务规则（Phase 1）。
3. 当提供代码或 API 时，补充分析实现逻辑、异常处理和契约风险（Phase 2）。
4. 当系统存在明显状态流转或复杂业务规则时，建立领域模型与状态模型（Phase 3）。
5. 当复杂度足够高时，进一步执行 MBT 导向测试设计（Phase 4）。
6. 生成结构化测试用例、场景清单和追溯输出（Phase 5）。
7. 在交付前依据质量检查项进行校验。

只需轻量结果时走降级路径：快速测试点清单、场景梳理、边界条件清单、回归建议。

## 执行模式

| 模式 | 适用输入 | 重点关注 |
|---|---|---|
| **需求驱动** | PRD、需求文档、用户故事、自然语言功能描述 | 功能拆解、验收条件、边界条件、正常与异常场景 |
| **代码辅助** | 源代码、仓库文件、接口实现、服务逻辑、API 处理代码 | 控制流、数据流、异常路径、契约风险、隐藏分支与潜在缺陷点 |
| **MBT 导向** | 复杂状态流转、审批链路、订单或支付生命周期、角色权限分支、规则密集型流程 | 业务实体与状态模型、转换条件与非法路径、覆盖准则、用例规模控制 |
| **回归聚焦** | 缺陷描述、修复背景、补丁上下文、事故复盘信息 | 受影响路径、邻近风险、边界回归、负向场景、接口兼容性 |

模式可叠加：仅需求文本 → 需求驱动；需求 + 代码 → 需求驱动 + 代码辅助；存在状态流转或复杂规则 → 叠加 MBT 导向；提供缺陷或补丁 → 回归聚焦。用户只想快速获得思路时，走轻量路径而不强行跑完整流水线。

## 执行规则

执行时始终遵守以下规则：

- 不要凭空编造需求、业务规则或预期结果；如果必须推断，明确标记为"推断"或"假设"。
- 始终保留来源与结论之间的追溯关系。
- 优先写出可执行、可验证的预期结果，避免空泛描述。
- 明确区分"已确认信息"和"推断信息"。
- 当关键信息缺失时，先报告缺口，再决定是否输出降级版本。
- 如果代码实现与需求描述冲突，优先把代码视为当前实现，同时显式指出需求不一致。
- 质量优先于数量，避免生成大量低价值或重复用例。
- 术语一旦确定，全程保持一致。

## 质量门禁

在最终交付前，至少检查：

- 可测试需求是否得到覆盖 ｜ 场景是否具备可执行性 ｜ 预期结果是否可观察、可验证
- 边界条件是否被覆盖 ｜ 负向路径是否被遗漏 ｜ 重复用例是否被控制
- 是否建立了必要的追溯关系 ｜ 假设项是否被清楚标记 ｜ 术语与结构是否前后一致

如果输入质量不足以支撑正式交付，先返回 **① 风险摘要 ② 缺失信息清单 ③ 如仍有价值再给出降级版测试草稿**。

交付前的必做评审动作见 [`references/quality-review.md`](references/quality-review.md)。

## 资源路由

不要把所有细节都堆在本文件中，按需读取配套资源。

### 阶段提示词 `prompts/`

需要详细阶段化执行时，读取对应文件：

- `prompts/phase0_input_preprocessing_prompt.md`
- `prompts/phase1_requirements_prompt.md`
- `prompts/phase2_code_analysis_prompt.md`
- `prompts/phase3_domain_analysis_prompt.md`
- `prompts/phase4_mbt_design_prompt.md`
- `prompts/phase5_testcase_generation_prompt.md`

### 补充参考 `references/`

- [`references/delivery-protocol.md`](references/delivery-protocol.md) —— 最小交付协议、输出字段与用例类别、输出风格、三种交付深度
- [`references/quality-review.md`](references/quality-review.md) —— 交付前必做的质量评审动作、能力边界与约束
- [`references/knowledge-base-usage.md`](references/knowledge-base-usage.md) —— 本地知识库录入、触发词与 `[参考知识]` 消费规则

### 模板 `templates/`

需要输出结构化结果时使用：

- `templates/requirements_template.md` ｜ `templates/state_diagram_template.md` ｜ `templates/testcase_template.md`

### 参考资源 `resources/`

- `resources/output_artifacts.md` —— 各阶段产物清单与阻断规则
- `resources/quality_checklist.md` —— 质量检查项与权重
- `resources/testcase_formats.md` —— 多格式输出参考
- `resources/feedback_template.md` —— 反馈闭环模板

### 格式选择准则

- **正式交付 / 审计 / 跨团队评审**：用 `templates/testcase_template.md` 的标准完整格式，保留追溯、前置条件、测试数据、步骤与可二元判定的预期结果。
- **快速评审 / Smoke 清单 / 早期需求讨论**：用简洁表格或测试点清单，但必须标记为"测试草稿"或"测试点清单"，不得声称为正式测试用例。
- **BDD / 业务协作**：用 Gherkin，至少含 Feature、Scenario、Given、When、Then；Then 必须描述可观测结果。
- **API / 契约测试**：明确 Request、Expected Response、状态码、响应 Schema、错误矩阵与鉴权/权限分支。
- **大量参数组合**：用数据驱动格式，分离测试逻辑与测试数据，并说明边界值、等价类与组合策略。

### 配置 `config/`

当用户提供配置或要求定制输出行为时，读取 `config/testcase-config-schema.json` 与 `config/example-config.json`。

### 本地文件支持 `scripts/`

输入为本地需求文件、PRD 或混合结构文档时可用：

- `scripts/prd_reader.py` —— Markdown / PDF 解析（**可选依赖**；宿主不能执行脚本时降级为纯文本分析）
- `scripts/incremental_code_scan.py` —— git diff / patch / PR 与 PRD 联合分析：提取新增代码行、判断是否符合 PRD、识别潜在 bug 风险
