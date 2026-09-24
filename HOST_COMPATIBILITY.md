# 宿主兼容性说明

本文档说明 `testcase-generator` 在不同大模型工具/宿主中的适配策略、能力边界和降级方式。

## 设计原则

当前项目采用：

- 根目录作为 canonical source
- `SKILL.md` 作为中文主入口
- `skill.manifest.json` 作为统一分发与宿主路由元数据
- `adapters/` 作为宿主薄适配层

适配层只负责：

- 宿主入口文件名适配
- 触发场景与语言表达适配
- 资源路由说明
- 能力降级说明

适配层不复制核心 prompts、templates、resources、config。

## 宿主适配入口

| 宿主 | 入口文件 | 语言策略 | 推荐程度 |
|---|---|---|---|
| Claude 类宿主 | `adapters/claude/SKILL.md` | 中文主说明 + 英文 trigger phrases | 高 |
| Qoder / IDE 类宿主 | `adapters/qoder/SKILL.md` | 中文主说明 + 工程化入口 | 高 |
| CodeBuddy / 腾讯云 AI 代码助手 | `adapters/codebuddy/SKILL.md` | 中文主说明 + 英文 trigger phrases | 高 |
| Codex / 工程 CLI 类宿主 | `adapters/codex/AGENTS.md` | 英文主说明 + 中文补充 | 中 |
| OpenClaw / 兼容型宿主 | `adapters/openclaw/skill.md` | 简化英文入口 + 中文补充 | 中 |
| Cursor / Anysphere | `adapters/cursor/cursorrules.md` | 英文为主 + 中文补充，激活时复制为 `.cursorrules` | 中（软适配） |
| Windsurf / Antigravity（Codeium / Google） | `adapters/windsurf/windsurfrules.md` | 英文为主 + 中文补充，激活时复制为 `.windsurfrules` | 中（软适配） |

## Node.js 激活入口

通过 npm 安装后，可使用 `test-generator activate all` 一次性激活所有支持的宿主环境，也可使用 `test-generator activate <environment>` 将 Skill 运行时文件复制到单个对应宿主目录。

| 环境名 | 默认本地目标目录 | 额外入口 |
|---|---|---|
| `claude` | `.claude/skills/testcase-generator` | 根目录 `SKILL.md` |
| `qoder` | `.qoder/skills/testcase-generator` | 根目录 `SKILL.md` |
| `codex` | `.agents/skills/testcase-generator` | 根目录 `AGENTS.md` |
| `openclaw` | `skills/testcase-generator` | 根目录 `skill.md` |
| `trae` | `.trae/skills/testcase-generator` | 根目录 `SKILL.md` |
| `codebuddy` | `.codebuddy/skills/testcase-generator` | 根目录 `SKILL.md` |
| `cursor` | `.cursor/rules/` | 根目录 `.cursorrules`（来自 `adapters/cursor/cursorrules.md`） |
| `windsurf` | `.windsurf/rules/` | 根目录 `.windsurfrules`（来自 `adapters/windsurf/windsurfrules.md`） |

可通过 `-g` 安装到用户本地目录，或通过 `--target <path>` 指定单个平台目标目录。`--target` 不支持 `activate all`，避免多个宿主写入同一个精确目录。`--global` 仍作为兼容写法保留。

### 大小写不敏感文件系统上的入口冲突

OpenClaw 的约定入口是 `skill.md`，而 canonical 入口是 `SKILL.md`。在 Windows / macOS
这类**大小写不敏感**的文件系统上，两者指向**同一个文件**——照常写入适配器会把
canonical `SKILL.md` 直接覆盖掉。

因此 `test-generator activate openclaw` 检测到该冲突时会**跳过**写入 `skill.md`，
保留 canonical `SKILL.md`，并输出明确提示：

```text
Host entry: skipped 'skill.md' — on case-insensitive filesystems it is the same file
as 'SKILL.md'; the canonical file was kept.
```

适配器本身仍随运行时文件落到目标目录的 `adapters/openclaw/skill.md`，能力不受影响。
在大小写敏感的 Linux 上两个文件可以共存，不会触发该保护。

## 能力差异与降级策略

不同宿主对 Skill 的支持能力不同，必须允许优雅降级。

### 1. 多文件导航能力

- **支持多文件导航**：可按根目录 `SKILL.md`、`prompts/`、`resources/`、`templates/` 完整执行
- **仅支持入口文件**：adapter 必须明确告诉宿主优先读取哪些文件

### 2. 脚本执行能力

- **支持脚本执行**：可使用 `scripts/prd_reader.py` 读取本地 PRD / Markdown / PDF；可使用 `scripts/incremental_code_scan.py` 扫描 diff 新增代码行并结合 PRD 输出符合性与潜在 bug 信号
- **不支持脚本执行**：降级为纯文本分析模式，直接基于用户提供的文本或已读取文件内容执行

### 3. 语言能力差异

- 中文优先宿主：直接使用根目录 `SKILL.md` 或 Claude/Qoder adapter
- 英文优先宿主：优先使用 Codex/OpenClaw adapter，并依赖双语 manifest 辅助识别

## 宿主具体建议

### Claude

适合：
- 复杂测试设计
- 多文件路由
- PRD + 代码联合分析
- MBT 导向建模

建议：
- 优先读取 `adapters/claude/SKILL.md`
- 然后再导航到根目录 `SKILL.md` 和 `prompts/`

### Qoder

适合：
- 仓库内多文件工程分析
- 代码与需求联合测试设计
- 结构化测试用例产出

建议：
- 优先读取 `adapters/qoder/SKILL.md`
- 当脚本不可执行时，明确回落到文本分析模式

### Codex

适合：
- 英文偏好的工程化任务
- 基于 AGENTS.md 的轻量入口

限制：
- 对中文主文档的触发准确率可能低于中文宿主
- 对多文件资源的自动导航不一定稳定

建议：
- 优先读取 `adapters/codex/AGENTS.md`
- adapter 中明确 required files 和 fallback behavior

### OpenClaw

适合：
- 可注入 workspace prompt 的环境
- 需要保守型 skill 入口的场景

建议：
- 使用最小入口 `adapters/openclaw/skill.md`
- 如果宿主不支持脚本，则只走文本与模板驱动路径

### CodeBuddy（腾讯云 AI 代码助手）

适合：
- 仓库内多文件联合分析
- PRD + 代码联合测试设计
- IDE 协作语境下的中文任务

入口约定：
- 入口文件固定为 `SKILL.md`
- 宿主目录固定为 `.codebuddy/skills/testcase-generator/`

建议：
- 优先读取 `adapters/codebuddy/SKILL.md`
- 与 Claude / Qoder 共用 `prompts/` 与 `resources/` 资源；不需要复制核心资产
- 脚本不可执行时显式回落到纯文本分析模式

### Cursor（Anysphere，软适配）

适合：
- 使用 `.cursorrules` 风格的单文件规则的 IDE/编辑器场景
- 上下文预算有限、需要快速产出的轻量任务

入口约定：
- 入口文件为 `adapters/cursor/cursorrules.md`
- 激活时由 `test-generator activate cursor` 复制为根目录 `.cursorrules`

建议：
- 完整复杂任务仍然回退到根目录 `SKILL.md` + `prompts/`
- 上下文紧张时按 cursorrules 中的 Fallback 策略输出测试点清单
- 软适配不复制核心资产

### Windsurf / Antigravity（Codeium / Google，软适配）

适合：
- 使用 `.windsurfrules` 风格的单文件规则的 IDE/编辑器场景
- 多模型协作 / 英文偏好环境

入口约定：
- 入口文件为 `adapters/windsurf/windsurfrules.md`
- 激活时由 `test-generator activate windsurf` 复制为根目录 `.windsurfrules`

建议：
- 与 Cursor 软适配类似：完整任务回退到根目录 `SKILL.md`，上下文紧张时按 Fallback 策略
- 不要在 `.windsurfrules` 中复制核心 prompts / templates / resources

## 推荐接入方式

### 中文工作流

优先顺序：
1. 根目录 `SKILL.md`
2. `adapters/claude/SKILL.md`
3. `adapters/qoder/SKILL.md`
4. `adapters/codebuddy/SKILL.md`

### 英文或混合工作流

优先顺序：
1. `adapters/codex/AGENTS.md`
2. `adapters/openclaw/skill.md`
3. `adapters/cursor/cursorrules.md`（Cursor 软适配）
4. `adapters/windsurf/windsurfrules.md`（Windsurf / Antigravity 软适配）
5. `skill.manifest.json` 中的英文元数据

## 后续建议

当前已经具备 canonical source + host adapters 的基础结构。后续可以继续推进：

1. 在打包阶段按宿主生成专用分发包
2. 为 Codex / OpenClaw / Cursor / Windsurf 增加更严格的英文 trigger phrase 测试
3. 为 Claude / Qoder / CodeBuddy 增加多文件路由自测用例
4. 为 Cursor / Windsurf rules 文件补一份 `devtools/` 下的 syntax lint（确保不漂移到核心方法论）
5. 跟进 Kimi / Lingma / MarsCode / 文心快码等宿主是否有新的 skill / rules 入口约定
