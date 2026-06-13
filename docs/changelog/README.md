# Changelog — 变更记录

> 版本变更、破坏性改动、迁移指南。

## 当前状态

- 历史变更日志在 [`.harness/changelogs/`](../../.harness/changelogs/) 下，但目前只覆盖 harness 体系内部。
- Skill 本体的版本变更在 [`../../SKILL.md`](../../SKILL.md) 顶部 YAML frontmatter 里记录（`version: 2.1.0`）。
- npm 包版本在 [`../../package.json`](../../package.json) 的 `version` 字段。

## 待写内容

- [ ] **README.md**：版本索引（v2.x → 主要变化 → 迁移指南）
- [ ] **v2.2.0.md**：下一个版本的计划变更（待 skill-author 启动）
- [ ] **migration-v1-to-v2.md**：v1 → v2 的迁移指南（如有 v1 用户）

## 维护规则

每次发版必须：

1. 更新 `../../SKILL.md` 的 `version`
2. 更新 `../../package.json` 的 `version`
3. 更新 `../../skill.manifest.json` 的 `版本`
4. 在本目录新建 `v<新版本>.md` 记录主要变化
5. 在 `.harness/changelogs/` 同步对应记录

这四份文件必须保持版本号一致 —— [`.harness/scripts/doc_consistency_audit.py`](../../.harness/scripts/doc_consistency_audit.py) 会自动检查。
