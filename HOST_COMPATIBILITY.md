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
| Codex / 工程 CLI 类宿主 | `adapters/codex/AGENTS.md` | 英文主说明 + 中文补充 | 中 |
| OpenClaw / 兼容型宿主 | `adapters/openclaw/skill.md` | 简化英文入口 + 中文补充 | 中 |

## 能力差异与降级策略

不同宿主对 Skill 的支持能力不同，必须允许优雅降级。

### 1. 多文件导航能力

- **支持多文件导航**：可按根目录 `SKILL.md`、`prompts/`、`resources/`、`templates/` 完整执行
- **仅支持入口文件**：adapter 必须明确告诉宿主优先读取哪些文件

### 2. 脚本执行能力

- **支持脚本执行**：可使用 `scripts/prd_reader.py` 读取本地 PRD / Markdown / PDF
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

## 推荐接入方式

### 中文工作流

优先顺序：
1. 根目录 `SKILL.md`
2. `adapters/claude/SKILL.md`
3. `adapters/qoder/SKILL.md`

### 英文或混合工作流

优先顺序：
1. `adapters/codex/AGENTS.md`
2. `adapters/openclaw/skill.md`
3. `skill.manifest.json` 中的英文元数据

## 后续建议

当前已经具备 canonical source + host adapters 的基础结构。后续可以继续推进：

1. 为每个宿主增加自动导出脚本
2. 在打包阶段按宿主生成专用分发包
3. 为 Codex / OpenClaw 增加更严格的英文 trigger phrase 测试
4. 为 Claude / Qoder 增加多文件路由自测用例
