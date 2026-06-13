# Development — 开发指南

> 改 prompts / templates / adapters / 评测规则时看这里。

## 待写内容

- [ ] **contributing.md**：贡献流程、PR checklist、Code Review 规范
- [ ] **adding-host-adapter.md**：如何新增一个 AI 宿主适配器（含 manifest / adapters/ / lib/activation.js 三处同步点）
- [ ] **prompts-authoring.md**：prompts 编写规范（输入契约、输出契约、调用上下文）
- [ ] **templates-authoring.md**：templates 修改规范（不要破坏下游解析）
- [ ] **local-dev-loop.md**：本地调试流程（devtools/ 下工具链如何使用）

## 修改前的检查清单

任何对以下文件的修改，都必须同时检查对应位置：

| 改动位置 | 同步检查 |
|---|---|
| `prompts/phaseN_*.md` | `resources/output_artifacts.md`（产物协议）+ `.harness/eval/baselines/`（回归基线） |
| `templates/*.md` | `SKILL.md` 中对该模板的引用 |
| `adapters/<host>/` | `skill.manifest.json` → `宿主适配入口` + `HOST_COMPATIBILITY.md` |
| `SKILL.md` 描述行 | `skill.manifest.json` → `说明` 字段、`README.md` → 顶部 GitHub Topics |
| `config/*.json` | `test-fixtures/skill-eval/` 下的样例需同步更新 |

## 调试工具

- [`../../devtools/capability_audit.py`](../../devtools/capability_audit.py) — 能力审计（打包前必跑）
- [`../../devtools/skill_quality_audit.py`](../../devtools/skill_quality_audit.py) — Skill 内容质量审计
- [`../../test/activation.test.js`](../../test/activation.test.js) — Node.js 激活逻辑单测
- [`../../test/test_skill_quality_audit.py`](../../test/test_skill_quality_audit.py) — Python 工具单测
- [`../../.harness/scripts/doc_consistency_audit.py`](../../.harness/scripts/doc_consistency_audit.py) — 文档一致性审计
