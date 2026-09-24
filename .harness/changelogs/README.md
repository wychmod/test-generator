# .harness/changelogs/ — 变更日志规范

本目录是 `testcase-generator` 的发版日志仓库。每一份文件都是**给人
看的**——不需要机器解析，但格式要保持一致。

## 命名规范

| 模式 | 何时创建 | 内容状态 |
|---|---|---|
| `v<MAJOR>.<MINOR>.<PATCH>.md` | 发版当次 | 完整回填（新增 / 改动 / 修复 / 移除 / 已知限制 / 升级注意） |
| `v<MAJOR>.<MINOR>.<PATCH>-TEMPLATE.md` | 下一个计划中的版本 | 占位模板，发版日重命名为正式文件名 |
| `v<MAJOR>.<MINOR>.<PATCH>-draft.md` | 开发期 | 自由格式，PR 阶段合并入正式 `v*.md` |

文件名中的 `MAJOR.MINOR.PATCH` **必须**与 `SKILL.md` / `README.md` /
`skill.manifest.json` 三处版本号完全一致。

## 必含字段

每份正式 `v<版本号>.md` 必须包含以下六节（顺序固定）：

1. **版本 / 发布日期 / 状态** —— 在 front matter 写明。
2. **新增**（Added）—— 任何新增的能力、提示词、模板、宿主、命令。
3. **改动**（Changed）—— 既有能力的行为变化、字段重命名、默认值调整。
4. **修复**（Fixed）—— 用户可见的 bug 修复，标注 issue 编号（如有）。
5. **移除**（Removed）—— 任何被删除的能力、宿主、字段。**不写**就
   表示本版没移除。
6. **已知限制**（Known Limitations）—— 本版未解决但已知的问题，附
   解封条件的 issue 链接。
7. **升级注意**（Upgrade Notes）—— 升级本版需要做的迁移动作、配置
   变更、宿主侧指令更新。

如果某一节没有内容，明确写「无」而不是删除整节——下游读者会按节扫读。

## 模板

复制 `v2.4.0-TEMPLATE.md` 重命名为目标版本号（去掉 `-TEMPLATE`），
然后逐节填入。

## 何时回填

- **发版当日**：把 `-draft.md` 改名为正式 `vX.Y.Z.md`，并把内容收口。
- **下一版启动时**：复制最新已发版文件为 `v<NEW>-TEMPLATE.md`，清空
  各节内容（保留节标题），作为新版本的工作基线。
- **不要删除**历史 `v*.md` 文件——它们是 changelog 的 changelog。

## 例子

仓库当前已回填 `v2.1.0.md`、`v2.2.0.md`（已发布，2026-06-15）与
`v2.3.0.md`（当前版本）。

`v2.3.0.md` 的内容已经收口，`status` 仍为 `draft` —— 只差发布动作
（`npm publish` + GitHub Release）。发布当日把 `status` 改为 `stable`
并补 `released` 日期即可。

下一版的工作基线是 `v2.4.0-TEMPLATE.md`。如果想看更早的历史，请参考
`README.md` 的「版本历史」章节。

> **注意**：`version_alignment` 只比对版本字符串，无法发现"版本升了但发版日志没回填"。
> 这类问题由 `changelog_exists` 检查兜底 —— 当前 manifest 版本必须有对应的正式
> `v<版本>.md`，只存在 `-TEMPLATE` / `-draft` 会直接 fail。
