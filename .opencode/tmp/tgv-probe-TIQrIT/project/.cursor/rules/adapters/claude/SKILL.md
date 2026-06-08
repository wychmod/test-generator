---
name: testcase-generator-claude-adapter
description: 适配 Claude 类宿主的入口文件。Use when the host expects a SKILL.md-style entry and can navigate multiple files. Trigger for requests about generating, reviewing, expanding, or standardizing test cases, test scenarios, or MBT-oriented testing outputs.
---

# Claude Adapter for Testcase Generator

这是 `testcase-generator` 的 Claude 类宿主适配入口。

## 适用场景

当用户提出以下需求时触发：
- 根据 PRD、需求文档、API、代码生成测试用例
- 评审或补全测试场景
- 进行 MBT 导向测试设计
- 输出结构化测试设计文档

## 使用方式

1. 优先理解根目录 `SKILL.md` 的核心规则。
2. 根据任务类型继续读取：
   - `prompts/` 中的阶段提示词
   - `resources/` 中的质量与格式规范
   - `templates/` 中的输出模板
3. 若输入为本地 PRD / Markdown / PDF 文件，可在宿主支持脚本时使用 `scripts/prd_reader.py`。

## 推荐路由

- 完整复杂任务：读取根目录 `SKILL.md` + `prompts/` + `resources/quality_checklist.md`
- 轻量任务：读取根目录 `SKILL.md` + `templates/testcase_template.md`
- 输入质量较差：先参考 `resources/output_artifacts.md` 中的阻断与假设规则

## Fallback

如果宿主不能稳定执行脚本：
- 直接基于用户提供的文本内容执行
- 不依赖 `scripts/prd_reader.py`
- 明确标记基于文本推断的假设项
