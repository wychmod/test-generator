---
name: testcase-generator-qoder-adapter
description: 适配 Qoder 或 IDE 集成类宿主的入口文件。Use when the host works inside a repository, can inspect files, and needs an engineering-oriented entry for test case generation, requirement review, code-assisted testing, or structured testcase outputs.
---

# Qoder Adapter for Testcase Generator

这是面向 Qoder / IDE 集成类宿主的适配入口。

## 重点能力

Qoder 类宿主更适合：
- 仓库内多文件联合分析
- PRD + 代码联合测试设计
- 接口与实现逻辑的对照检查
- 结构化测试用例产出

## 推荐读取顺序

1. 根目录 `SKILL.md`
2. 与任务相关的 `prompts/phase*.md`
3. `resources/quality_checklist.md`
4. `templates/testcase_template.md`

## 适配说明

- 代码辅助模式优先于纯需求模式，当代码与需求同时存在时优先结合两者。
- 宿主如果支持读取多个仓库文件，应同时查看需求、实现、配置和接口定义。
- 不要求一定能执行 `scripts/prd_reader.py`；如果不能执行，直接走文本分析路径。

## 降级策略

当宿主不支持脚本或某些文件无法读取时：
- 输出测试点清单或轻量结构化用例
- 明确说明缺失输入和假设项
- 不伪造完整交付物
