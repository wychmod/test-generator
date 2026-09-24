---
name: testcase-generator-zencoder-adapter
description: 适配 Zencoder 的入口文件。Use when the host is Zencoder and expects a SKILL.md-style entry under its skills directory, and needs an entry for test case generation, requirement review, code-assisted testing, or structured testcase outputs.
---

# Zencoder Adapter for Testcase Generator

这是 `testcase-generator` 在 **Zencoder** 中的适配入口。

## 适配依据

Zencoder 官方技能目录为项目级 `.zencoder/skills/<name>/SKILL.md`、用户级 `~/.zencoder/skills/<name>/SKILL.md`，因此本技能**无需格式转换**即可被发现 ——
适配层只需完成入口命名、触发词与资源路由。

## 适用场景

当用户提出以下需求时触发：

- 根据 PRD、需求文档、API 规范或代码生成测试用例
- 评审、补全或标准化已有的测试场景与测试点清单
- 进行 MBT 导向的测试设计（状态机、覆盖准则、路径集）
- 基于 diff / patch 做增量回归测试设计

## 使用方式

1. 优先理解技能根目录 `SKILL.md` 的核心规则、执行模式与资源路由。
2. 按任务类型继续读取：
   - `prompts/` —— 六阶段提示词（`phase0` ~ `phase5`）
   - `references/` —— 交付协议、质量评审动作、知识库消费规则
   - `resources/` —— 质量清单、输出格式参考、阶段产物协议、反馈模板
   - `templates/` —— 需求 / 状态图 / 测试用例模板
3. 输入为本地 PRD / Markdown / PDF 时，若宿主能执行脚本，可用
   `scripts/prd_reader.py`；有 diff / patch 时可用
   `scripts/incremental_code_scan.py`。

## 推荐路由

| 任务规模 | 读取内容 |
|---|---|
| 完整复杂任务 | `SKILL.md` + `prompts/` + `resources/quality_checklist.md` |
| 轻量任务 | `SKILL.md` + `templates/testcase_template.md` |
| 输入质量较差 | 先读 `resources/output_artifacts.md` 的阻断与假设规则 |
| 需要参考项目规范 | `references/knowledge-base-usage.md` + `knowledge/` |

## Fallback

Zencoder **不保证** Python 运行时可用。若脚本无法执行：

- 直接基于用户提供的文本内容执行分析，不依赖 `scripts/` 下的任何脚本
- 明确标记基于文本推断的假设项
- 缺失的输入先报告缺口，再决定是否输出降级版本（测试点清单 / 风险摘要）

**绝不**因为脚本不可用而伪造完整交付物。
