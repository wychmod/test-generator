# Testcase Generator — 文档中心

本目录收纳所有非分发的内部文档。**根目录保留的 4 份 Markdown 是分发包必需**，其余说明、流程、规范都集中在此。

## 文档地图

| 类别 | 路径 | 内容 | 状态 |
|---|---|---|---|
| **用户入口** | [`../README.md`](../README.md) | 安装、快速开始、用法 | 必读 |
| **Skill 主入口** | [`../skills/testcase-generator/SKILL.md`](../skills/testcase-generator/SKILL.md) | Skill 入口文件、能力声明、触发场景 | 必读 |
| 分发边界 | [`../DISTRIBUTION.md`](../DISTRIBUTION.md) | 入包/排除规则、发布前检查 | 必读 |
| 宿主兼容 | [`../HOST_COMPATIBILITY.md`](../HOST_COMPATIBILITY.md) | 各宿主适配策略、Node.js 激活命令 | 必读 |
| **打包指南** | [`operations/packaging.md`](operations/packaging.md) | 如何本地打包、产物校验 | 已搬入 |
| 测试计划 | [`quality/test-plan.md`](quality/test-plan.md) | 评测维度、行业基准 | 已搬入 |

> **关于根目录的 4 份 Markdown**：`SKILL.md` / `README.md` / `DISTRIBUTION.md` / `HOST_COMPATIBILITY.md` 位于仓库根目录是**有意的** —— `package.json` 的 `files` 字段、`devtools/package_skill.py` 的 `REQUIRED_ARCHIVE_MEMBERS`、`test/activation.test.js` 都硬编码了它们的根路径。请勿移动。

## docs/ 子目录

### `architecture/` — 架构与设计
设计意图、模块边界、数据流。开发新能力时优先看这里。

### `operations/` — 运维与发布
打包、发布、宿主激活、CI 等流程文档。

### `development/` — 开发指南
如何修改 prompts / templates / adapters，如何新增宿主适配器，本地调试流程。

### `quality/` — 质量与评测
测试计划、质量门禁、评审 checklist、回归基线。

### `changelog/` — 变更记录
历史版本变更、计划中的破坏性改动。

## 文档写作约定

1. **中文为主**。Skill 是中文优先产品。
2. **每个目录放一个 README.md** 作为该目录的入口，避免成为「野文件目录」。
3. **跨文档链接用相对路径**（例如 `../SKILL.md`），不要用绝对 URL，避免 GitHub 渲染问题。
4. **改分发边界前**必须同步更新 `../DISTRIBUTION.md` 和 `../skill.manifest.json`。
5. **改 `skills/testcase-generator/` 下的 SKILL.md / prompts/ / resources/ / templates/ 前**先在 `.harness/eval/` 加一条评测用例，确保改动有回归保护。

## 待办

- [ ] `architecture/pipeline-overview.md`：六阶段流水线详解（当前只在 SKILL.md 简述）
- [ ] `development/contributing.md`：贡献流程 + PR checklist
- [ ] `development/adding-host-adapter.md`：新适配器开发指南
- [ ] `development/prompts-authoring.md`：prompts 编写规范
- [ ] `quality/quality-gates.md`：质量门禁如何运转、各阶段产物如何评分
- [ ] `changelog/README.md`：版本变更索引
