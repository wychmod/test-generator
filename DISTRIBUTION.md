# 分发清单

本文档定义 `testcase-generator` 作为可拔插 Skill 分发时的入包边界、排除规则与发布检查项。

## 分发目标

将当前项目整理为一个可安装、可迁移、可复用的测试用例生成 Skill 包。

推荐产物名：

```text
testcase-generator.skill
```

兼容产物名：

```text
testcase-generator.zip
```

Node.js/npm 产物名（npm 包名带 `@wychmod-cn/` scope）：

```text
@wychmod-cn/testcase-generator-skill
```

> 如果宿主平台支持标准 Skill 包，优先使用 `.skill`；仅在宿主平台只接受 ZIP 时再使用 `.zip`。
> npm 产物用于提供 `test-generator activate all` 和 `test-generator activate <environment>` 激活命令，不改变 `.skill` / `.zip` 的入包边界。

## 必须入包

以下文件和目录属于 Skill 运行时资产，必须进入分发包。

| 路径 | 用途 |
|---|---|
| `skills/testcase-generator/SKILL.md` | Skill 入口文件，负责触发说明、执行规则与资源路由 |
| `skills/testcase-generator/config/` | 配置 Schema 与示例配置 |
| `skills/testcase-generator/prompts/` | 六阶段分析与生成提示词 |
| `skills/testcase-generator/references/` | 交付协议、质量评审动作、知识库使用等按需加载的补充参考（渐进披露第三层） |
| `skills/testcase-generator/resources/` | 质量检查、格式规范、反馈模板与阶段产物协议 |
| `skills/testcase-generator/templates/` | 需求、状态图、测试用例等标准输出模板 |
| `skills/testcase-generator/scripts/prd_reader.py` | 本地 PRD / Markdown / PDF 文件读取辅助工具 |
| `skills/testcase-generator/scripts/incremental_code_scan.py` | 增量 diff 代码行扫描、PRD 符合性分析与潜在 bug 信号辅助工具 |
| `README.md` | 面向使用者和维护者的说明文档 |
| `skill.manifest.json` | 中文分发元数据与入包边界说明 |

> 技能运行时内容统一位于 **`skills/testcase-generator/`**（Agent Skills 标准布局），
> 客户端可自动发现；仓库根的其余目录属于分发元数据或开发工具，不是技能内容。

## npm 分发必须入包

以下文件属于 Node.js/npm 安装入口，必须进入 npm 包，但不进入标准 `.skill` / `.zip` 运行时分发包。

| 路径 | 用途 |
|---|---|
| `package.json` | npm 元数据、`bin` 命令入口与发布文件清单 |
| `bin/test-generator.js` | `test-generator` 命令行入口 |
| `lib/activation.js` | 宿主环境激活、运行时文件复制与目标目录解析 |

## 建议排除

以下内容不应进入最终分发包。

| 路径 | 排除原因 |
|---|---|
| `test-output/` | 本地验证产物，不属于运行时资产 |
| `docs/` | 内部文档中心与 README 图表源（`docs/assets/diagrams/`），不是 Skill 运行时资产。**显式声明**，此前仅因不在运行时白名单内而被顺带排除 |
| `.harness/` | AI 协作治理体系（项目宪法 / reins 角色契约 / 文档护栏脚本 / 评测流水线），属于开发元数据而非 Skill 运行时资产。**显式声明** |
| `skills/testcase-generator/knowledge/index.json` | 本地生成的 BM25 索引，由 `build_index.py` 产出，不入包 |
| `.claude/` | Claude 宿主镜像副本，避免重复和版本漂移 |
| `.agents/` | Amp / Codex 宿主镜像副本，避免重复和版本漂移 |
| `.commandcode/` | Command Code 宿主镜像副本，避免重复和版本漂移 |
| `.qoder/` | Qoder 宿主镜像副本，避免重复和版本漂移 |
| `.trae/` | Trae 宿主镜像副本，避免重复和版本漂移 |
| `.codebuddy/` | CodeBuddy 宿主镜像副本，避免重复和版本漂移 |
| `.cursor/` | Cursor 宿主镜像副本，避免重复和版本漂移 |
| `.windsurf/` | Windsurf 宿主镜像副本，避免重复和版本漂移 |
| `.opencode/` | OpenCode 宿主镜像副本，避免重复和版本漂移 |
| `.cline/` | Cline 宿主镜像副本，避免重复和版本漂移 |
| `.roo/` | Roo Code 宿主镜像副本，避免重复和版本漂移 |
| `.kilocode/` | Kilo Code 宿主镜像副本，避免重复和版本漂移 |
| `.gemini/` | Gemini CLI / Google Antigravity 宿主镜像副本，避免重复和版本漂移 |
| `.qwen/` | Qwen Code 宿主镜像副本，避免重复和版本漂移 |
| `.kiro/` | Kiro 宿主镜像副本，避免重复和版本漂移 |
| `.factory/` | Factory Droid 宿主镜像副本，避免重复和版本漂移 |
| `.goose/` | Goose 宿主镜像副本，避免重复和版本漂移 |
| `.openhands/` | OpenHands 宿主镜像副本，避免重复和版本漂移 |
| `.github/` | GitHub Copilot 宿主镜像副本，避免重复和版本漂移 |
| `.agent/` | Google Antigravity 宿主镜像副本，避免重复和版本漂移 |
| `.pi/` | Pi 宿主镜像副本，避免重复和版本漂移 |
| `.mcpjam/` | MCPJam 宿主镜像副本，避免重复和版本漂移 |
| `.zencoder/` | Zencoder 宿主镜像副本，避免重复和版本漂移 |
| `.openclaw/` | OpenClaw 宿主镜像副本，避免重复和版本漂移 |
| `.clawdbot/` | Clawdbot 宿主镜像副本，避免重复和版本漂移 |
| `.clinerules/` | Cline 兼容规则目录，避免重复和版本漂移 |
| `.workbuddy/` | 本地工作记忆与环境配置，不能分发 |
| `.git/` | 版本控制目录，不能分发 |
| `.idea/` | IDE 本地配置，不能分发 |
| `.venv/` | 本地 Python 环境，不能分发 |
| `__pycache__/` | Python 缓存，不能分发 |
| `devtools/` | 开发与发布工具（capability_audit / package_skill 等），不属于 Skill 运行时能力 |
| `bin/test-generator.js` | npm CLI 入口，只进入 npm 包，不进入运行时分发 |
| `lib/activation.js` | npm 激活逻辑，只进入 npm 包，不进入运行时分发 |
| `devtools/capability_audit.py` | 审计工具，不属于 Skill 运行时能力（devtools/ 已整体排除） |
| `devtools/package_skill.py` | 打包工具，不属于 Skill 运行时能力（devtools/ 已整体排除） |
| `_pkg_log.txt` | 本地打包日志，不能分发 |
| `_pkg_result.txt` | 本地打包结果，不能分发 |
| `package_log.txt` | 本地打包日志，不能分发 |
| `skills-lock.json` | 宿主侧锁定文件，不属于 Skill 运行时资产 |
| `testcase-generator.zip` | 兼容打包产物，避免包中包 |
| `testcase-generator.skill` | 标准打包产物，避免包中包 |
| `skills/testcase-generator/knowledge/index.json` | 本地知识库索引产物（`build_index.py` 本地构建），不进包 |

## 开发工具处理

以下文件建议保留在仓库，且**不进入**运行时分发包。

| 当前路径 | 建议长期位置 | 说明 |
|---|---|---|
| `devtools/package_skill.py` | `devtools/package_skill.py` | 打包工具，不属于 Skill 运行时能力 |
| `devtools/capability_audit.py` | `devtools/capability_audit.py` | 审计工具，不属于普通使用场景 |
| `bin/test-generator.js` | `bin/test-generator.js` | npm CLI 入口，只进入 npm 包，不进入 `.skill` / `.zip` |
| `lib/activation.js` | `lib/activation.js` | npm 激活逻辑，只进入 npm 包，不进入 `.skill` / `.zip` |
| `run_package.bat` | `devtools/run_package.bat` | Windows 打包入口，不属于运行时资产 |
| `PACKAGING.md` | `docs/operations/packaging.md`（**已搬入**，根目录不再保留） | 发布维护说明，不属于 Skill 执行资产 |

当前阶段已经完成开发工具迁移；后续如需进一步收口，可再将 `run_package.bat` 与发布文档统一收纳到 `devtools/` / `docs/`。

## 运行时资产（进入分发包）

以下内容**会**进入 `.skill` / `.zip`，与 `skill.manifest.json` 的"运行时文件"保持一致。
它们**不是**排除项 —— 不要从分发包中剔除，否则会丢失知识库辅助层。

| 路径 | 说明 |
|---|---|
| `knowledge/README.md` | 知识库用户文档 |
| `knowledge/llm-ingest-template.md` | 可直接复制给大模型的知识录入模板 |
| `knowledge/sources/README.md` | sources 使用说明 |
| `skills/testcase-generator/knowledge/sources/*.md`（示例） | 示例源文件（domain-glossary / project-conventions / historical-cases）；用户后续填充的内容不进包 |
| `skills/testcase-generator/knowledge/scripts/build_index.py` | 索引构建工具（宿主支持 Python 时可用） |
| `skills/testcase-generator/knowledge/scripts/search.py` | BM25 检索工具（宿主支持 Python 时可用） |
| `skills/testcase-generator/knowledge/scripts/ingest.py` | 知识录入工具（依赖用户自配置的 LLM 命令） |

## 推荐分发包内容树

```text
testcase-generator/
├── skills/
│   └── testcase-generator/          # ← 技能树（Agent Skills 标准布局，客户端自动发现）
│       ├── SKILL.md
│       ├── config/
│       │   ├── example-config.json
│       │   └── testcase-config-schema.json
│       ├── prompts/
│       │   ├── phase0_input_preprocessing_prompt.md
│       │   ├── phase1_requirements_prompt.md
│       │   ├── phase2_code_analysis_prompt.md
│       │   ├── phase3_domain_analysis_prompt.md
│       │   ├── phase4_mbt_design_prompt.md
│       │   ├── phase5_testcase_generation_prompt.md
│       │   └── knowledge_ingest_prompt.md
│       ├── references/
│       │   ├── delivery-protocol.md
│       │   ├── quality-review.md
│       │   └── knowledge-base-usage.md
│       ├── resources/
│       │   ├── feedback_template.md
│       │   ├── output_artifacts.md
│       │   ├── quality_checklist.md
│       │   └── testcase_formats.md
│       ├── templates/
│       │   ├── requirements_template.md
│       │   ├── state_diagram_template.md
│       │   └── testcase_template.md
│       ├── scripts/
│       │   ├── prd_reader.py
│       │   └── incremental_code_scan.py
│       └── knowledge/
│           ├── README.md
│           ├── llm-ingest-template.md
│           ├── sources/
│           │   ├── README.md
│           │   ├── domain-glossary.md
│           │   ├── project-conventions.md
│           │   └── historical-cases.md
│           └── scripts/
│               ├── build_index.py
│               ├── ingest.py
│               └── search.py
├── adapters/                        # ← 宿主薄适配入口（不进技能树）
├── README.md
└── skill.manifest.json
```

## 发布前检查项

发布前逐项确认：

- [ ] `skills/testcase-generator/SKILL.md` 位于分发包内（Agent Skills 标准布局）。
- [ ] `SKILL.md` 主体内容为中文。
- [ ] `SKILL.md` 的 description 能覆盖主要触发场景。
- [ ] `skills/testcase-generator/resources/output_artifacts.md` 存在，且承接详细阶段产物说明。
- [ ] 技能树下的 `config/`、`prompts/`、`references/`、`resources/`、`templates/`、`scripts/`、`knowledge/` 均已入包。
- [ ] `skills/testcase-generator/knowledge/index.json` **未**入包。
- [ ] 本地验证产物 `test-output/` 未入包。
- [ ] 多宿主镜像目录未入包。
- [ ] 本地工作记忆 `.workbuddy/` 未入包。
- [ ] 分发包内不存在 `skills-lock.json`、旧 ZIP 或包中包。
- [ ] 同时生成 `.skill` 与 `.zip` 两种产物，且内容一致。
- [ ] npm 包包含 `package.json`、`bin/`、`lib/` 和 Skill 运行时资产。
- [ ] `test-generator activate all --dry-run` 与 `test-generator activate <environment> --dry-run` 可显示正确目标目录。
- [ ] 抽样打开包内 Markdown，确认中文内容未乱码。

## 后续建议

后续可以把打包脚本升级为读取 `skill.manifest.json` 的 include / exclude 规则，避免脚本和文档规则分叉。
