---
name: testcase-generator-codebuddy-adapter
description: 适配 CodeBuddy（腾讯云 AI 代码助手）类宿主的入口文件。Use when the host expects a SKILL.md-style entry under `.codebuddy/skills/<name>/`, can navigate multiple files in a repository, and needs an engineering-oriented entry for test case generation, requirement review, code-assisted testing, or structured testcase outputs. Trigger for requests about generating, reviewing, expanding, or standardizing test cases, test scenarios, or MBT-oriented testing outputs in CodeBuddy.
---

# CodeBuddy Adapter for Testcase Generator

这是 `testcase-generator` 在腾讯云 **CodeBuddy**（AI 代码助手）类宿主中的适配入口。

## 适用场景

当用户使用 CodeBuddy（或同源工具）提出以下需求时触发：

- 根据 PRD、需求文档、API、代码生成测试用例
- 评审、补全、扩展或标准化已有测试用例与测试场景
- 进行 MBT 导向测试设计、状态机建模
- 输出结构化测试设计文档、追溯矩阵、质量门禁报告

## 使用方式

1. 优先阅读本入口（`adapters/codebuddy/SKILL.md`）确定本环境的资源路由与降级策略。
2. 继续读取仓库根目录 `SKILL.md` 的核心规则与执行模式。
3. 根据任务类型按需读取：
   - `prompts/phase0_input_preprocessing_prompt.md` ~ `prompts/phase5_testcase_generation_prompt.md`
   - `resources/quality_checklist.md`、`resources/output_artifacts.md`、`resources/testcase_formats.md`
   - `templates/testcase_template.md`、`templates/requirements_template.md`、`templates/state_diagram_template.md`
4. 若输入是本地 PRD / Markdown / PDF 文件，且 CodeBuddy 允许执行脚本时，可使用 `scripts/prd_reader.py`。

## 重点能力

CodeBuddy 类宿主在以下场景表现稳定：

- 仓库内多文件联合分析（代码 + 需求 + 接口 + 配置）
- PRD + 代码联合测试设计
- 接口与实现逻辑的对照检查、契约风险识别
- 状态机 / 业务规则 / 审批链路等 MBT 导向测试设计
- 仓库内结构化测试用例产出（Markdown / Gherkin / JSON）

## 推荐路由

- 完整复杂任务：根目录 `SKILL.md` + `prompts/phase0..phase5` + `resources/quality_checklist.md` + `resources/output_artifacts.md`
- 轻量任务：根目录 `SKILL.md` + `templates/testcase_template.md`
- 代码与需求同时存在：根目录 `SKILL.md` + `prompts/phase1_requirements_prompt.md` + `prompts/phase2_code_analysis_prompt.md`
- 输入质量较差：先参考 `resources/output_artifacts.md` 中的阻断与假设规则，再决定是否输出降级版本

## 适配说明

- 默认入口文件名是 `SKILL.md`，宿主目录约定为 `.codebuddy/skills/testcase-generator/`（项目级）或 `~/.codebuddy/skills/testcase-generator/`（用户级）。
- 与 Claude / Qoder 适配器相比，CodeBuddy 更偏向 IDE 内联协作；建议在仓库语境下启用代码辅助模式（Phase 2）。
- 兼容 `scripts/prd_reader.py`；若宿主限制脚本执行，回落到纯文本分析路径并显式标记假设项。
- 不复制核心 prompts / templates / resources / config；仅作为入口与降级说明。

## Fallback

当 CodeBuddy 不可执行脚本、不可读取多文件或上下文窗口受限时：

- 改为基于用户提供的文本内容执行，不依赖 `scripts/prd_reader.py`
- 主动声明输入缺失、推断与假设项
- 输出可降级为测试点清单、测试草稿、场景梳理或边界条件清单
- 不要伪造完整交付物；遵循 `SKILL.md` 中“最小交付协议”的字段要求

## 与其他适配器的关系

- 与 `adapters/claude/SKILL.md` 结构对齐，可视为 CodeBuddy 在中文 IDE 场景下的对等入口。
- 与 `adapters/qoder/SKILL.md` 共享工程化入口风格；差异在于 CodeBuddy 入口文件名固定为 `SKILL.md`，且宿主目录固定为 `.codebuddy/skills/`。
- 仓库根目录始终是 canonical source；本 adapter 不重新定义核心方法论，只调整触发场景、入口与降级策略。
