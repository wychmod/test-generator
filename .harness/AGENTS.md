# 项目宪法 — testcase-generator

> 位置：`.harness/AGENTS.md`
> 范围：仅对 `D:\pycharm\test-generator` 仓库生效
> 读者：所有 AI 协作 agent、本项目 reins（见 `.harness/reins/`）以及新接手的工程师
> 语言：中文优先

---

## 1. 项目是什么

`testcase-generator` 是一个**生产级 AI 测试用例生成 Skill**，当前版本以 `skill.manifest.json` 的"版本"字段为准（写作时 **v2.3.0**）。

- 它是一个 Skill 包（不是普通库），技能树位于 **`skills/testcase-generator/`**（Agent Skills 标准布局），以其中的 `SKILL.md` 作为中文主入口，根目录 `skill.manifest.json` 作为统一分发与宿主路由元数据。
- 核心方法论是 **MBT（Model-Based Testing）+ 六阶段流水线**：
  - **Phase 0 输入预处理 → Phase 1 需求预处理 → Phase 2 代码分析 → Phase 3 领域建模 → Phase 4 MBT 设计 → Phase 5 用例生成**。
- 支持多种输入：需求文档、PRD、用户故事、API 规范、源代码、缺陷修复上下文、功能描述、本地 Markdown/PDF 文件。
- 支持多宿主分发：**26 个宿主**（完整清单见根目录 `HOST_COMPATIBILITY.md`）；通过 `test-generator activate <env>` 命令将运行时文件复制到对应宿主目录。
- 同时维护两条分发链：
  - 运行时 Skill 分发：`.skill` / `.zip`
  - npm CLI 分发：`@wychmod-cn/testcase-generator-skill`（`test-generator` 命令）

---

## 2. 目录速查表

仓库根目录的 canonical source 结构如下。**任何 agent 在改动前必须先确认改动落在哪一列**。

| 路径 | 作用 | 是否入包 | 备注 |
|---|---|---|---|
| `skills/testcase-generator/` | **技能树（canonical）**：SKILL.md + prompts / references / resources / templates / config / scripts / knowledge | 是 | Agent Skills 标准布局，客户端自动发现；**必须被 git 跟踪** |
| `skills/testcase-generator/SKILL.md` | 中文主入口，描述/触发/执行规则/资源路由 | 是 | 入包于技能树内 |
| `README.md` | 面向使用者和维护者的说明文档 | 是 | 入包根目录 |
| `skill.manifest.json` | 机器可读的中文分发元数据（运行时文件、分发排除、宿主入口、版本源） | 是 | 入包根目录 |
| `DISTRIBUTION.md` | 人工可读的分发清单与发布检查项 | 是 | 入包根目录 |
| `HOST_COMPATIBILITY.md` | 宿主兼容性矩阵与能力降级说明 | 是 | 入包根目录 |
| `docs/operations/packaging.md` | 打包与发布说明 | **否** | dev 工具说明文档（原根目录 `PACKAGING.md`，已搬入 `docs/operations/`） |
| `adapters/` | 多宿主薄适配层（**26 个宿主**，完整清单见 `HOST_COMPATIBILITY.md`） | 是 | 不复制技能树内容 |
| `skills/testcase-generator/config/` | JSON Schema 与示例配置 | 是 | `testcase-config-schema.json` + `example-config.json` |
| `skills/testcase-generator/prompts/` | 6 个阶段提示词（phase0..phase5）+ 知识入库提示词 | 是 | AI 实际执行的指令源 |
| `skills/testcase-generator/references/` | 按需加载的补充参考（渐进披露第三层） | 是 | 交付协议 / 质量评审 / 知识库用法 |
| `skills/testcase-generator/resources/` | 质量检查、格式规范、反馈模板、阶段产物协议 | 是 | `quality_checklist.md` / `output_artifacts.md` / `testcase_formats.md` / `feedback_template.md` |
| `skills/testcase-generator/templates/` | 需求/状态图/测试用例输出模板 | 是 | 3 个模板 |
| `skills/testcase-generator/scripts/prd_reader.py` | 本地 PRD / Markdown / PDF 读取辅助 | 是 | **可选依赖**，宿主不支持 Python 时降级为文本分析 |
| `devtools/` | 能力审计 / 质量审计 / 打包脚本 | **否** | 永远不入包；放在仓库内便于发布前验证 |
| `bin/test-generator.js` | npm CLI 入口（`test-generator` 命令） | 仅 npm | 不入 `.skill` / `.zip` |
| `lib/activation.js` | npm 激活逻辑（`ENVIRONMENTS` 常量、`activateEnvironment`） | 仅 npm | 不入 `.skill` / `.zip` |
| `test/` | node 单测 + Python 审计测试 | **否** | CI 跑，不入包 |
| `docs/` | 内部测试计划等开发文档 | **否** | 不入包 |
| `test-output/` | 本地验证产物 | **否** | **永远不能入包** |
| `run_package.bat` | Windows 打包入口 | **否** | 已被 `python devtools/package_skill.py` 替代 |
| `.harness/` | 本目录：AI 协作宪法 + reins + 文档护栏 + 评测流水线 | **否** | 开发工具元数据，**不能**入包（已显式列入 manifest「分发排除」） |
| `.github/workflows/` | CI 流水线（required check） | **否** | 开发基础设施 |

> 关键设计：**`skills/testcase-generator/` 是技能内容的 canonical source**（Agent Skills 标准布局，客户端自动发现），`adapters/` 是**薄适配层**（只适配入口文件名、触发场景和降级说明，不复制核心 prompts/templates/resources）。各宿主目录（`.claude/`、`.codebuddy/` 等）是 `test-generator activate` 命令**生成的产物**，全部已 gitignore。

---

## 3. 必跑命令

| 命令 | 用途 | 何时跑 |
|---|---|---|
| `python devtools/sync_version.py` | 版本单一数据源（以 `skill.manifest.json` 为准，`--check` 报漂移 / `--write` 一键回写） | 任何改版本号的动作前必跑 |
| `python devtools/gen_plugin_manifests.py` | 客户端插件清单生成（`.claude-plugin/plugin.json` + `marketplace.json`，源同为 `skill.manifest.json`） | 改 manifest / package.json 后必跑 |
| `python devtools/capability_audit.py` | 能力矩阵审计（Schema 有效、必需路径、版本对齐、版本同步、能力标记、宿主入口） | 改动 SKILL.md / prompts / resources / templates 后必跑 |
| `python devtools/skill_quality_audit.py` | Skill 字段质量审计（用例字段、阶段流水线、标准引用、版本漂移） | 改动 prompt / template / quality_checklist 后必跑 |
| `python devtools/package_skill.py` | 打包（先跑能力审计预检，再生成 `.skill` + `.zip` 并交叉校验） | 发布前必跑；改 manifest 排除规则后必跑 |
| `python .harness/scripts/doc_consistency_audit.py` | 文档护栏（版本号一致、能力矩阵覆盖、宿主表三方一致、npm 入口、排他规则一致、运行时清单、技能树内路径写法、**`.harness/` 自身一致性**） | 改动 SKILL.md / README / manifest / HOST_COMPATIBILITY / DISTRIBUTION / 任何 adapter / **任何 `.harness/` 文档** 后必跑 |
| `node --test <显式文件列表>` | node 单测（`activation.test.js` 覆盖激活解析与复制；`adapter-routing.test.js` 覆盖 manifest ↔ ENVIRONMENTS ↔ adapters 三方一致；`test-discovery.test.js` 守卫脚本与测试文件集合一致） | 改 `lib/activation.js` / `bin/test-generator.js` / `skill.manifest.json` 的宿主入口后必跑 |
| `node bin/test-generator.js environments` | 列出所有支持的宿主（**26 个**；清单以 `lib/activation.js` 的 `ENVIRONMENTS` 为准） | 改动 `ENVIRONMENTS` 常量后必跑 |
| `node bin/test-generator.js activate <env> --dry-run` | dry-run 激活，输出目标目录和文件数，不写盘 | 改激活逻辑后必跑 |
| `npm test` | node 单测套件（**显式文件列表**，见 `package.json`；不要写成 glob —— `node --test` 的 glob 支持是 Node v21 才有的，会挂掉 CI 的 18/20） | CI / 发布前 |
| `npm run test:python` | Python 单测套件（`unittest discover -s test -p "test_*.py"`，覆盖增量扫描、知识库、质量审计、manifest 字段对齐） | 改 `skills/testcase-generator/scripts/` / `.../knowledge/` / `devtools/` 后必跑 |
| `python .harness/eval/run_eval.py` | 端到端离线评测（`test-fixtures/skill-eval/` 的 12 个 fixture → 校验阶段提示词覆盖、能力声明与产物路径） | 改 `prompts/` / `templates/` 后必跑；CI 已接入（非 `--strict`：CI 无 `test-output/`，产物检查退化为 warn 是预期行为） |

> 四层防御：capability_audit（声明层） + skill_quality_audit（内容层） +
> doc_consistency_audit（结构层，含 `.harness/` 自身）+ eval（端到端），
> 任何改动都要让这些层全绿，否则不能合并。前四者均为 CI required check。

---

## 4. AI 协作铁律（绝对不能违反）

### 4.0 canonical 技能树铁律

**`skills/testcase-generator/` 是技能内容的唯一来源，必须被 git 跟踪。**

- 它**不是**镜像目录。`/skills/` 已从 `.gitignore` 移除，并已从 manifest `分发排除`
  与 `package_skill.py` 的 `FORBIDDEN_ARCHIVE_PATTERNS` 中移除。
- 各客户端的激活产物是点号开头的宿主目录（`.claude/`、`.agents/` …），不是这里。
- 技能树内的文件若要引用技能树**外**的文件（如仓库的 `docs/`），需要跨三层：
  `../../../docs/...`。

### 4.1 入包边界铁律

以下目录和文件**永远不能**进入 `.skill` / `.zip` 分发包：

> **权威清单是 `skill.manifest.json` 的「分发排除」字段**（当前 48 项），
> 下表是分组速查。新增宿主时必须同步「宿主镜像副本」组与 manifest。

| 路径 | 原因 |
|---|---|
| `.claude/` `.codebuddy/` `.codex/` `.cursor/` `.qoder/` `.trae/` `.windsurf/` `.agents/` `.opencode/` `.cline/` `.roo/` `.kilocode/` `.gemini/` `.qwen/` `.kiro/` `.factory/` `.goose/` `.openhands/` `.github/` `.agent/` `.pi/` `.mcpjam/` `.zencoder/` `.openclaw/` `.clawdbot/` `.clinerules/` | **宿主镜像副本**（26 个宿主的激活产物），避免重复和版本漂移 |
| `.workbuddy/` | 本地工作记忆与环境配置 |
| `test-output/` | 本地验证产物 |
| `skills-lock.json` | 宿主侧锁定文件 |
| `testcase-generator.zip` / `testcase-generator.skill` | 打包产物（包中包） |
| `.git/` / `.github/` | 版本控制与 CI 目录 |
| `.idea/` / `.venv/` / `__pycache__/` | 本地环境目录 |
| `devtools/` | 打包 / 审计工具，不属于运行时 |
| `.harness/` | AI 协作元数据，**不属于运行时资产**（已显式列入 manifest「分发排除」） |
| `docs/` | 开发文档，不属于运行时资产（已显式列入 manifest「分发排除」） |

> 注意：`.github/` 同时出现在两行中（既非宿主编译产物、也非版本控制目录的严格意义上属 CI），
> 它在 manifest 里以 `.github/**` 形式登记。

### 4.2 版本号三处一致铁律

版本号的唯一数据源是 **`skill.manifest.json` 的"版本"字段**，其余位置一律由同步器回写，不允许手工各改各的：

- `SKILL.md` front matter 必须有 `version: X.Y.Z`
- `README.md` 第一行标题必须包含 `vX.Y.Z`
- `skill.manifest.json` 的"版本"字段必须是 `X.Y.Z`（**数据源**）
- `prompts/` / `resources/` / `templates/` 里的 `> **版本**` 抬头、`template_version`、`generated_by`、文档 H1 标题等身份标记同样必须一致

升级版本的**唯一正确姿势**：

1. 改 `skill.manifest.json` 的"版本"。
2. 跑 `python devtools/sync_version.py --write` 回写全部身份标记。
3. 跑 `python devtools/sync_version.py` 确认零漂移。

发版前**必须**跑 `python .harness/scripts/doc_consistency_audit.py` 验证三处一致；
`capability_audit.py` 的 `version_sync` 项会在打包预检阶段再次拦截漂移。

> 注意：`[vX.Y 新增]` / `vX.Y 增强内容` 属于**历史归属标记**，记录"该能力是哪一版引入的"，
> 禁止随版本号一起改；外链里的 `v2.1.0`（Postman / SARIF 规范 URL）同样不得改动。

### 4.3 adapter 薄适配铁律

`adapters/<host>/*` 入口文件**只做四件事**：

1. 宿主入口文件名适配（`SKILL.md` / `AGENTS.md` / `skill.md`）
2. 触发场景与语言表达适配
3. 资源路由说明（指向根目录 `SKILL.md` / `prompts/` / `resources/` / `templates/`）
4. 能力降级说明（脚本不可执行时怎么办、多文件导航不可用时怎么办）

adapter **不能**：
- 复制 `prompts/` / `templates/` / `resources/` 的实际内容
- 在 adapter 中重新定义核心方法论
- 修改或覆盖根目录 `SKILL.md` 的规则

### 4.4 中文优先铁律

- `SKILL.md` 主体内容必须为中文（front matter 的 `description` 可以包含中英双语）
- 所有 reins 的 `AGENT.md` 必须中文
- `DISTRIBUTION.md` / `HOST_COMPATIBILITY.md` / `docs/operations/packaging.md` 必须中文
- `README.md` 主体中文，代码块内可含英文命令
- 适配器中：Claude / Qoder 中文优先；Codex / OpenClaw 英文优先但需中文补充

### 4.5 能力矩阵不能分叉铁律

`SKILL.md` 声明的能力 ↔ `prompts/phase*.md` ↔ `resources/output_artifacts.md` ↔ `skill.manifest.json` 的"核心能力"字段 必须保持一致。

具体地，**核心能力清单**（zh-CN 7 项）：

1. 输入质量预处理
2. 可测试需求抽取
3. 代码与接口契约辅助分析
4. 领域模型与状态模型构建
5. MBT 导向测试设计
6. 结构化测试用例生成
7. 追溯矩阵与质量门禁

新增能力时，必须同时更新这四个地方。删除能力同理。

### 4.6 prd_reader.py 是可选依赖铁律

`scripts/prd_reader.py` 是**可选**依赖——宿主支持 Python 时可使用，否则降级为纯文本分析模式。

- 在 `SKILL.md` / `adapters/*` 中提到 prd_reader 时，**必须**同时说明降级路径
- 任何 adapter 都必须包含 "Fallback" 段，说明脚本不可执行时如何处理
- 不允许让 prd_reader 成为强制依赖

### 4.7 reins 协作铁律

- 所有 reins **必须**先读本文件，再读自己的 `AGENT.md`
- reins 之间通过**文件改动 + 跑命令验证**的方式协作，不通过 chat 互调
- 任何 reins 发现自己负责范围之外的问题，写入对应 reins 的 issue 清单中（由 packager / auditor 在 PR 阶段汇总）
- reins 的产出物格式由各自的 `AGENT.md` 定义，**必须**遵守

---

## 5. PR 模板

```markdown
## 改了什么
- <一句话描述>

## 关联的 reins
- <skill-author / adapter-curator / manifest-keeper / packager / auditor / test-runner / 跨多个>

## 跑过的验证
- [ ] `python devtools/capability_audit.py` 全绿
- [ ] `python devtools/skill_quality_audit.py` 全绿
- [ ] `python .harness/scripts/doc_consistency_audit.py` 全绿
- [ ] `npm test` 全绿（显式文件列表，勿写成 glob）
- [ ] `npm run test:python` 全绿
- [ ] `python .harness/eval/run_eval.py` 无退化（如涉及 prompts / templates）
- [ ] `node bin/test-generator.js environments` 输出与改动一致
- [ ] `node bin/test-generator.js activate <env> --dry-run` 目标目录正确（如涉及激活逻辑）

## 触及的铁律
- [ ] 入包边界铁律（未引入新禁入项）
- [ ] 版本号三处一致（如改版本号，三处同时改）
- [ ] adapter 薄适配（未在 adapter 中复制核心内容）
- [ ] 中文优先
- [ ] 能力矩阵一致（如改能力清单）
- [ ] prd_reader 可选依赖（如改 prd_reader 逻辑）

## 决策点
- <如果有，记录权衡过程>
```

---

## 6. reins 角色索引

完整定义见 `.harness/reins/README.md`。本表为速查。**当前 6 个 reins**。

| reins | 主责 | 关键产出 |
|---|---|---|
| `skill-author` | `skills/testcase-generator/` 下的 SKILL.md / prompts/ / templates/ / resources/ / references/ 维护 | 阶段提示词 / 模板 / 资源文件的更新 |
| `adapter-curator` | adapters/ 维护（26 宿主），与技能树 SKILL.md 同步 | 薄适配文件 + 触发场景对齐 |
| `manifest-keeper` | skill.manifest.json + DISTRIBUTION.md 一致性 | manifest / 排除规则 / 必需文件清单 |
| `packager` | 跑 `devtools/package_skill.py`，验证 `.skill` / `.zip` 一致 | 双产物交叉校验报告 |
| `auditor` | 跑 capability_audit + skill_quality_audit + doc_consistency_audit | 三层审计全绿报告 |
| `test-runner` | 跑 `npm test` + `npm run test:python` + `python .harness/eval/run_eval.py`，验证 `lib/activation.js` 在所有宿主下激活路径正确、评测基线不退化 | 单测报告 + 宿主路径快照 + 评测报告 |

> reins 是**人/AI 协作角色契约**，不是可执行程序。它们通过"文件改动 + 跑命令验证"协作，
> 不通过脚本互调 —— 因此 `reins/` 目录**不会被任何脚本引用**，这是设计使然，不是死代码。
> 评测（eval）职责并入 `test-runner`，不单设第 7 个角色。

---

## 7. 相关文档链接

| 文档 | 作用 |
|---|---|
| [`.harness/README.md`](./README.md) | `.harness/` 总览与文件结构 |
| [`.harness/reins/README.md`](./reins/README.md) | reins 角色清单与新增流程 |
| [`.harness/scripts/README.md`](./scripts/README.md) | 护栏脚本使用说明 |
| [`.harness/eval/README.md`](./eval/README.md) | 端到端评测流水线说明 |
| [`../AGENTS.md`](../AGENTS.md) | 仓库根操作说明（面向 AI agent，含必跑命令与已踩过的坑） |
| [`../DISTRIBUTION.md`](../DISTRIBUTION.md) | 分发清单与发布检查项 |
| [`../HOST_COMPATIBILITY.md`](../HOST_COMPATIBILITY.md) | 宿主兼容性矩阵（26 宿主的权威清单） |
| [`../docs/operations/packaging.md`](../docs/operations/packaging.md) | 打包与发布详细说明 |
| [`../skills/testcase-generator/SKILL.md`](../skills/testcase-generator/SKILL.md) | 中文主入口 |
| [`../README.md`](../README.md) | 面向使用者的说明 |
| [`../skill.manifest.json`](../skill.manifest.json) | 机器可读的分发元数据（版本唯一数据源） |

---

## 8. 失败模式与升级路径

| 失败模式 | 谁负责 | 怎么修 |
|---|---|---|
| `capability_audit.py` fail | skill-author | 补齐缺失的 prompt / template / resource |
| `skill_quality_audit.py` fail | skill-author | 修必填字段或质量门禁 token |
| `doc_consistency_audit.py` fail | 对应 reins | 看具体项：版本号 → skill-author+manifest-keeper；能力 → skill-author；宿主表 → adapter-curator+manifest-keeper；排他 → manifest-keeper+packager；`.harness/` 自身 → 对应 reins |
| `npm test` fail | test-runner | 改 `lib/activation.js` 后重跑 |
| `npm run test:python` fail | test-runner | 看失败的测试模块，多数对应 `devtools/` 或技能树内脚本 |
| `run_eval.py` 退化 | test-runner | 补 `test-fixtures/skill-eval/` 基线或修 prompts |
| 打包后 `.skill` 与 `.zip` 内容不一致 | packager | 跑 `python devtools/package_skill.py` 重打包 |
| 宿主页面/CLI 提示与实际能力不符 | adapter-curator | 同步更新 HOST_COMPATIBILITY.md / adapter |
| 入包后发现包中包 / 镜像目录泄漏 | packager + manifest-keeper | 立即发版修复版本，并在 audit 中补强规则 |

> 任何失败都不允许绕过护栏脚本强行合并。

---

_本文件由 `.harness/` 体系维护；改动本文件需要同时更新本文件中的"必跑命令"和"reins 角色索引"两节，并在 PR 模板中勾选触及的铁律。
`doc_consistency_audit.py` 的 `harness_self_consistency` 检查会拦住本文件中的宿主数与版本号漂移。_
