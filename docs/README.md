# Testcase Generator — 文档中心

本目录收纳所有非分发的文档：内部说明、流程、规范，以及**对外发布的项目网站**。**根目录保留的 4 份 Markdown 是分发包必需**，其余内容都集中在此。

## 文档地图

| 类别 | 路径 | 内容 | 状态 |
|---|---|---|---|
| **用户入口** | [`../README.md`](../README.md) | 安装、快速开始、用法 | 必读 |
| **Skill 主入口** | [`../skills/testcase-generator/SKILL.md`](../skills/testcase-generator/SKILL.md) | Skill 入口文件、能力声明、触发场景 | 必读 |
| 分发边界 | [`../DISTRIBUTION.md`](../DISTRIBUTION.md) | 入包/排除规则、发布前检查 | 必读 |
| 宿主兼容 | [`../HOST_COMPATIBILITY.md`](../HOST_COMPATIBILITY.md) | 各宿主适配策略、Node.js 激活命令 | 必读 |
| **打包指南** | [`operations/packaging.md`](operations/packaging.md) | 如何本地打包、产物校验 | 已搬入 |
| 测试计划 | [`quality/test-plan.md`](quality/test-plan.md) | 评测维度、行业基准 | 已搬入 |
| **项目网站** | [`site/build.py`](site/build.py) | GitHub Pages 站点源码与构建器 | 已上线 |

> **关于根目录的 4 份 Markdown**：`SKILL.md` / `README.md` / `DISTRIBUTION.md` / `HOST_COMPATIBILITY.md` 位于仓库根目录是**有意的** —— `package.json` 的 `files` 字段、`devtools/package_skill.py` 的 `REQUIRED_ARCHIVE_MEMBERS`、`test/activation.test.js` 都硬编码了它们的根路径。请勿移动。
>
> `LICENSE` 同属根目录分发文件：`package.json` 的 `files`、`devtools/package_skill.py` 的入包白名单、`lib/activation.js` 的复制清单与 `DISTRIBUTION.md` 均已登记，由 `doc_consistency_audit.py` 的 `license_consistency` 项守卫，同样不要移动。

## docs/ 子目录

### `architecture/` — 架构与设计
设计意图、模块边界、数据流。开发新能力时优先看这里。
包含 [`architecture/agent-division/`](architecture/agent-division/README.md)：Agent 划分参考（不入包）——
把六阶段流水线拆成多 Agent 系统的契约层与编排层设计，供想构建 Agent 系统的人参照。

### `operations/` — 运维与发布
打包、发布、宿主激活、CI 等流程文档。

### `development/` — 开发指南
如何修改 prompts / templates / adapters，如何新增宿主适配器，本地调试流程。

### `quality/` — 质量与评测
测试计划、质量门禁、评审 checklist、回归基线。

### `changelog/` — 变更记录
历史版本变更、计划中的破坏性改动。

### `site/` — 项目网站
GitHub Pages 站点的源码：模板、样式与构建器。构建器从仓库真实内容
（`skill.manifest.json` 的版本与宿主清单、`architecture/agent-division/` 的 Agent 契约、
`prompts/` 的阶段提示词）渲染站点，因此**站点内容永远跟随仓库，不要手改产物**——
`index.html` / `agents.html` 与 `assets/site/` 都是 `python docs/site/build.py` 的输出。
线上地址 <https://wychmod.github.io/test-generator/>，提示词库在 `/agents.html`。

## 文档写作约定

1. **中文为主**。Skill 是中文优先产品。
2. **每个目录放一个 README.md** 作为该目录的入口，避免成为「野文件目录」。
3. **跨文档链接用相对路径**（例如 `../SKILL.md`），不要用绝对 URL，避免 GitHub 渲染问题。
4. **改分发边界前**必须同步更新 `../DISTRIBUTION.md` 和 `../skill.manifest.json`。
5. **改 `skills/testcase-generator/` 下的 SKILL.md / prompts/ / resources/ / templates/ 前**先在 `.harness/eval/` 加一条评测用例，确保改动有回归保护。

## 待办

- [ ] `development/prompts-authoring.md`：prompts 编写规范

> 原清单中的 `architecture/pipeline-overview.md`、`development/contributing.md`、
> `development/adding-host-adapter.md`、`quality/quality-gates.md`、`changelog/README.md`
> 均已落盘，已从待办移除。
