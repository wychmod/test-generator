# Skill 生态对标与改进方案

> 目的：用当前主流开源 Skill 项目的真实组织方式，校准 `testcase-generator` 的目录结构、分发与激活机制。
>
> 调研时间：2026-09-24 ｜ 对标对象：Agent Skills 标准、Agent Plugins 标准、Claude Code 插件规范、AGENTS.md 标准、obra/superpowers、skills.sh CLI
>
> 相关文档：[`pipeline-overview.md`](pipeline-overview.md) ｜ [`knowledge-base.md`](knowledge-base.md) ｜ [`../../HOST_COMPATIBILITY.md`](../../HOST_COMPATIBILITY.md) ｜ [`../../DISTRIBUTION.md`](../../DISTRIBUTION.md)

---

## 1. 结论摘要

生态已经收敛出**三层可复用的标准**：内容层（Agent Skills）、打包层（Agent Plugins / Claude Code 插件）、仓库上下文层（AGENTS.md）。`testcase-generator` 在**内容层与方法论深度上明显领先**，但完全自建了**打包层与激活层**，因此付出了两份代价：4.8 MB 的镜像冗余，以及已经真实发生过的镜像漂移。

最值得做的一件事：把已有的 `skill.manifest.json` 从"唯一的分发契约"降级为"**plugin.json 的生成源**"，让客户端原生安装器接管激活，从而彻底删掉 8 份镜像复制。

---

### 1.1 实施状态（2026-09-24 更新）

| 编号 | 事项 | 状态 |
|---|---|---|
| P0-1 | `.claude-plugin/` 插件清单（`skills: ["."]` 零迁移） | ✅ 已完成，由 `devtools/gen_plugin_manifests.py` 生成并纳入 CI |
| P0-2 | 根 `AGENTS.md`（≤100 行） | ✅ 已完成 |
| P0-3 | GitHub Actions CI（7 项必跑） | ✅ 已完成 |
| P1-5 | manifest 作为 plugin.json 的生成源 | ✅ 已完成（生成器 + `--check` + CI 门禁） |
| P1-6 | SKILL.md 瘦身到路由层 | ✅ 已完成：正文 6,045 → 3,906 字符（-35%），细则下沉 `references/` |
| P1-4 | 单一树 + 每客户端 manifest，替换 8 份镜像复制 | ⏸ **暂缓**（见下方"为何暂缓"） |
| P2-8 | 引入 agnix lint | ⏸ 未做：外部工具，需评估与自研审计的重叠度 |
| P2-9 | devtools 单测 | ✅ 已完成（`sync_version` / `gen_plugin_manifests` 共 20 例，Python 用例 15 → 36） |
| P2-10 | 收口 changelog + 版本↔changelog 守卫 | ✅ 已完成（新增 `changelog_exists` 审计项，已验证能拦截） |
| P2-11 | `.agents/skills/` 兼容层 | ✅ 已满足：`codex` 宿主的本地目标本就是 `.agents/skills/testcase-generator` |
| P2-7 | 发布到 skills.sh | ⏸ 依赖 P1-4 的 `skills/<name>/` 布局 |

**为何 P1-4 暂缓**：该改造需要同时改动 manifest 运行时路径、`lib/activation.js`、
4 个审计脚本中的硬编码路径、`package.json` 的 `files`、`README`/`DISTRIBUTION` 的目录树、
以及 skill 自身的资源路由（`prompts/` 是否改名 `references/`）。本地镜像虽达 4.8 MB，
但**全部在 `.gitignore` 内、不进入任何分发包**，因此它是"漂移风险"而非"分发缺陷"。
在 P0 的原生安装通路尚未在真机验证（`claude plugin validate`）之前就动结构，
会在生产 skill 上留下半破状态。建议作为独立版本（v2.3.0）推进。

---

## 2. 生态的三层标准

| 层 | 标准 | 作用 | 治理 |
|---|---|---|---|
| 内容层 | **Agent Skills**（`agentskills.io`） | 一个 Skill = 一个目录 + `SKILL.md`；渐进披露 | Anthropic 2025-10 提出，2025-12-18 发布为开放标准 |
| 打包层 | **Agent Plugins** v1.0.0（`agent-plugins.org`） | 把 Skills 与 MCP servers 打包成可移植插件 | TSC 含 Amazon / Cursor / Microsoft / OpenAI / Vercel |
| 打包层（厂商） | **Claude Code 插件 / 市场** | `.claude-plugin/plugin.json` + `marketplace.json` | Anthropic |
| 仓库上下文 | **AGENTS.md** | 仓库级 agent 指令 | OpenAI 2025-08 提出 → Linux Foundation 旗下 Agentic AI Foundation（2025-12-09） |

### 2.1 Agent Skills：内容层的硬约束

```
my-skill/
├── SKILL.md          # 必须：YAML frontmatter + Markdown 指令
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：按需加载的参考文档
└── assets/           # 可选：模板、资源
```

- frontmatter **只需要 `name` 与 `description`**；
- `description` 有 **1024 字符上限**（上传校验会拒绝超限）；
- `name` **不得包含保留词** `claude` / `anthropic`；
- **渐进披露**是核心机制，分三层：① 元数据（name + description）**常驻** system prompt，约 100 tokens；② SKILL.md 正文，命中后按需载入（建议 < 5,000 tokens）；③ `references/` 等附属文件，模型自行决定是否读取。
- 因此 SKILL.md 的角色是**路由与触发**，不是知识容器。

### 2.2 Agent Plugins：打包层的最小互操作面

```
my-plugin/
├── plugin.json                      # 必须
├── skills/<name>/SKILL.md           # Agent Skills 格式
├── mcp.json                         # MCP servers
└── com.example.client/hooks/        # 反域名命名空间：客户端私有扩展
```

关键设计：**共享部分用固定位置，客户端私有部分用反域名命名空间**。标准只约束"可移植的地板"，安装、权限、UX 仍归各客户端。

### 2.3 Claude Code 插件：目前最成熟的分发通路

- 清单：`.claude-plugin/plugin.json`（**仅 `name` 必需**）；**`.claude-plugin/` 里只允许放 manifest**，组件目录一律在插件根。
- 组件目录：`skills/`、`commands/`、`agents/`、`hooks/hooks.json`、`.mcp.json`、`.lsp.json`、`bin/`、`settings.json`。
- **`skills` 字段支持 `"."`** —— 意味着"根级 SKILL.md"这种单 Skill 布局也能直接当插件发布，无需挪文件。
- 市场：`.claude-plugin/marketplace.json`（`name` + `owner` + `plugins`）；plugin entry 至少 `name` + `source`。
- 插件来源支持 `relative path` / `github` / `url` / `git-subdir` / `npm` / `archive` / `command`。
- 路径用 `${CLAUDE_PLUGIN_ROOT}` 保持可移植；`bin/` 会加入 PATH。
- 用户侧安装：`/plugin marketplace add <repo>` → `/plugin install <name>@<marketplace>`。
- 2026-09-18 起（v2.1.277），仓库**没有 `CLAUDE.md` 时会回退读取 `AGENTS.md`**。

### 2.4 AGENTS.md：仓库上下文层

- 纯 Markdown，**无 schema、无 frontmatter**；仓库根（monorepo 可嵌套，**就近生效**）。
- **每次会话都会载入上下文**，所以官方与社区共识是**控制在 ~100 行以内**；自动生成的长文件被实证会**降低** agent 表现并推高 token 成本。
- 6 万+ 开源仓库采用，20~30+ 工具原生读取（Codex / Cursor / Copilot / Gemini CLI / Windsurf / Zed / Aider / Devin / Jules / Amp…）。

### 2.5 obra/superpowers：多客户端实践的最佳样本

这是与本项目定位最接近的项目（20+ 个 skill 的方法论框架），其多客户端策略值得直接借鉴：

```
superpowers/
├── .claude-plugin/     .codex-plugin/    .cursor-plugin/
├── .devin-plugin/      .hermes-plugin/   .kimi-plugin/
├── .muse-plugin/       .agents/plugins/  .opencode/
├── skills/          # ← 唯一的技能树
├── hooks/           # SessionStart 钩子注入引导
├── scripts/  tests/  docs/  assets/
└── .version-bump.json + scripts/bump-version.sh
```

要点：
- **一棵 `skills/` 树，每个客户端只加一个 manifest 目录** —— 没有整树复制。
- 用 `SessionStart` 钩子注入 `using-superpowers` 引导，保证技能按预期被触发。
- 版本靠 `.version-bump.json` + `bump-version.sh` 统一。
- 分发完全依赖各客户端的原生插件市场命令（`/plugin marketplace add`、`copilot plugin marketplace add`、`droid plugin install`…）。

### 2.6 skills.sh CLI：包管理器路线

- 通用安装：`npx skills add owner/repo`（或 `--skill <name>`、`-g` 全局）。
- **落盘策略：先装到通用目录 `~/.agents/skills/<name>/`，再 symlink 到各客户端目录**（`.claude/skills/`、`~/.cursor/skills/`）。一份文件，多客户端可见。
- `skills-lock.json` 用于可复现安装（`npx skills experimental_install`）；`skills list / update / remove / find / init` 构成完整生命周期。
- 注册表 skills.sh 已收录 9,500+ skills；安装时展示 Gen / Socket / Snyk 的安全评级。
- 补充：`agnix` 是社区做的 agent 配置 linter（156 条规则，覆盖 `SKILL.md` / `CLAUDE.md` / hooks / MCP，带自动修复与 LSP）。

---

## 3. 与当前架构的逐维对比

| 维度 | 生态主流 | `testcase-generator` 现状 | 判定 |
|---|---|---|---|
| 内容入口位置 | `skills/<name>/SKILL.md` | 根级 `SKILL.md` | ⚠ 单 Skill 可容忍，但不能直接进 skill 注册表 |
| 必需 frontmatter | `name` + `description` | `name` + `version` + `description` | ✅ 合规（多 `version` 无害） |
| `description` ≤ 1024 | 硬上限 | **388 字符** | ✅ 合规 |
| `name` 保留词 | 禁 `claude`/`anthropic` | `testcase-generator` | ✅ 合规 |
| 渐进披露 | SKILL.md + `references/` + `scripts/` + `assets/` | SKILL.md 路由到 `prompts/` `resources/` `templates/` `scripts/` | 🟡 机制一致，**命名不通用** |
| SKILL.md 体量 | 正文建议 < 5,000 tokens | **6,494 字符**（正文 6,045） | ⚠ 偏重，与渐进披露初衷有张力 |
| 打包清单 | `plugin.json` / `.claude-plugin/plugin.json` | 自研 `skill.manifest.json`（中文键） | ❌ 不在任何生态规范内 |
| 激活机制 | 客户端原生 `/plugin install` | 自研 `test-generator activate` 全量复制 | ❌ 用户需 `npm i` + `activate` 两步 |
| 多客户端策略 | 一棵树 + 每客户端一个 manifest | **8 份完整镜像副本** | ❌ 4.8 MB 冗余，已发生漂移 |
| 注册表分发 | skills.sh / 插件市场 | `.skill` / `.zip` + npm | 🟡 可达但非生态通路 |
| 锁文件 | `skills-lock.json` | 已有 | ✅ |
| 仓库上下文 | 根 `AGENTS.md`（就近生效） | `.harness/AGENTS.md`（非标准位置） | ⚠ 对本仓库贡献的 agent 读不到 |
| 质量护栏 | agnix 156 规则 / 客户端校验 | 自研 4 个审计脚本 + 2 套测试 | ✅ **领先** |
| 版本一致性 | git tag / `.version-bump.json` | manifest 单一数据源 + `sync_version` | ✅ **领先** |
| CI | GitHub Actions | 无 | ❌ 护栏靠人跑 |
| 安全扫描 | 客户端内置 Gen/Socket/Snyk | 无 | 🟡 可选 |

### 3.1 当前架构的优势（应当保留）

1. **方法论深度是真实护城河**。生态里绝大多数 Skill 是"一段 Markdown + 几份参考文档"；本项目有六阶段流水线、质量门 AC、MBT 建模、双向追溯矩阵、变异测试与混沌场景。这是差异化，不是包袱。
2. **显式的分发边界**。`运行时文件` 白名单 + `分发排除` + 打包后交叉校验，在生态里几乎没人做。多数项目靠 `.npmignore` 或 `.gitignore` 兜底。
3. **版本单一数据源 + 同步器**。生态普遍靠 git tag 与手工改号；本项目有 `sync_version.py --check/--write` 且已接入打包预检。
4. **四层可执行护栏**。阶段门 → 打包预检 → 文档一致性 → 单测，全部是脚本而非约定；`doc_consistency_audit.py` 能校验"文档与 manifest 是否互相矛盾"，这在生态里很超前。
5. **零依赖承诺**。Node 与 Python 两侧均无第三方依赖，跨宿主一致性与可分发性都好。
6. **渐进披露已实现**。SKILL.md 只做路由，重内容分文件承载 —— 方向与标准一致。

### 3.2 当前架构的不足

1. **打包层是孤岛**。`skill.manifest.json` 设计得很好，但没有任何客户端认识它。结果是用户必须走"装 npm 包 → 跑 activate"这条自研路径，而不能 `一行命令`安装。
2. **镜像复制而非单一树 + 多 manifest**。这是最大的结构性问题：8 × 44 文件、4.8 MB 冗余，而且**结构上允许漂移**——已经实测发生过（镜像停在 v2.1，缺 `knowledge/` 与增量扫描脚本）。修复只能是"每次发版记得重刷"，靠纪律维系。
3. **错过市场分发**。没有 `plugin.json` / `marketplace.json`，就无法被 Claude Code 插件市场、skills.sh 等收录，获客全靠 README 与 npm。
4. **根级 SKILL.md 布局**。单 Skill 场景可用（Claude Code 支持 `skills: ["."]`），但与 `skills/<name>/SKILL.md` 的主流约定不一致，进注册表需要改造。
5. **没有根 `AGENTS.md`**。`.harness/AGENTS.md` 内容质量很高（项目宪法 + 角色 + 护栏），但不在标准位置，对本仓库做贡献的 agent 反而读不到它。
6. **SKILL.md 偏重**。正文 6,045 字符，承担了核心能力、四种执行模式、执行规则、最小交付协议、质量评审、输出要求、质量门禁、资源路由、交付深度、约束等十余个章节。按标准的"SKILL.md 只做路由"原则，应把其中大部分下沉到 `references/`。
7. **无 CI**。三层审计与两套测试都靠人主动跑 —— 这正是 47 处版本漂移能长期积累的原因。

---

## 4. 改进方案

### P0 — 低成本高收益（建议先做，1–2 天）

#### P0-1 增加 Claude Code 插件清单，打通原生安装

**做法**（不移动任何文件）：新增 `.claude-plugin/plugin.json`：

```json
{
  "name": "testcase-generator",
  "displayName": "Testcase Generator",
  "description": "从需求 / PRD / API / 代码生成结构化可追溯的测试用例与 MBT 测试设计产物",
  "version": "2.2.0",
  "license": "MIT",
  "homepage": "https://github.com/wychmod/test-generator",
  "keywords": ["mbt", "testcase", "testing", "quality-assurance"],
  "skills": ["."]
}
```

`skills: ["."]` 表示"插件根目录本身就是一个 skill 目录"，正好匹配现有根级 `SKILL.md` 布局，**零文件迁移**。

再新增 `.claude-plugin/marketplace.json`：

```json
{
  "name": "wychmod-testcase-generator",
  "owner": { "name": "wychmod" },
  "plugins": [
    {
      "name": "testcase-generator",
      "source": "./",
      "description": "AI 驱动的测试用例生成 Skill（六阶段流水线 + MBT）",
      "version": "2.2.0"
    }
  ]
}
```

**预期收益**：用户从"`npm i` + `test-generator activate <host>`"两步，变为 `/plugin marketplace add wychmod/test-generator` → `/plugin install testcase-generator@wychmod-testcase-generator`；可直接上架 Claude Code 插件市场。

**约束**：`.claude-plugin/` 内**只放 manifest**；组件目录必须在插件根。

**验收**：`claude plugin validate` 通过；`.claude-plugin/` 仅含两个 JSON；新增 `devtools` 校验确保 `plugin.json` 的 `version` 与 `manifest.版本` 一致（可直接接进 `sync_version.py` 的规则表）。

#### P0-2 增加根 `AGENTS.md`，纳入既有护栏

**做法**：新增根 `AGENTS.md`，**≤ 100 行**，只放 agent 无法自行推断的内容：必跑命令、护栏铁律、目录边界、易踩的坑；完整项目宪法仍留在 `.harness/AGENTS.md`，在根文件里用一行指向它。

**预期收益**：Codex / Cursor / Copilot / Gemini CLI / Windsurf 等 20+ 工具开箱可用；Claude Code 在无 `CLAUDE.md` 时也会回退读取。对本仓库做贡献的 agent 首次能自动读到项目宪法。

**约束**：AGENTS.md **每会话注入上下文**，务必短。不要复制 `.harness/AGENTS.md` 全文。

#### P0-3 接入 CI，把护栏变成不可绕过

**做法**：新增 `.github/workflows/ci.yml`，五项设为 required check：

```
python devtools/sync_version.py
python devtools/capability_audit.py
python .harness/scripts/doc_consistency_audit.py
npm test
npm run test:python
```

**预期收益**：版本漂移、能力矩阵缺失、文档自相矛盾、测试失败在 PR 阶段即被拦截。这是把"靠自觉"变成"靠机器"的一步。

### P1 — 结构调整（3–5 天）

#### P1-4 用"单一树 + 每客户端 manifest"替换 8 份镜像复制

**做法**（参考 superpowers）：
1. 把 canonical 内容收敛为 `skills/testcase-generator/`（内含 `SKILL.md`、`references/`、`scripts/`、`assets/`）。
2. 每个客户端只加一个 manifest 目录：`.claude-plugin/`（P0-1 已建）、`.codex-plugin/`、`.cursor-plugin/` 等，全部**指向同一棵树**。
3. `adapters/<host>/*.md` 从"入口文件副本"降级为"manifest 中的路径引用"或直接删除；Agent Skills 的 `description` 触发词已覆盖大部分适配需求。
4. `lib/activation.js` 的复制逻辑保留为**本地开发 / 离线兜底**，但不再作为主分发机制。

**预期收益**：4.8 MB 冗余 → 0；镜像漂移从"结构性问题"变为"不可能发生"；`.gitignore` 里那 8 条镜像规则可以删掉。**这是消除已实测缺陷的根治手段。**

**风险与缓解**：Windows 下 symlink 不便（这也可能是当初选择复制的原因），因此**先做"生成"而非 symlink**——用脚本从单一树生成客户端视图，或直接依赖客户端各自的安装缓存（`~/.claude/plugins/cache`）。分阶段推进，先让 `.claude-plugin` 通路跑通再动其他客户端。

#### P1-5 把 `skill.manifest.json` 变成 plugin.json 的生成源

**做法**：保持 `skill.manifest.json` 作为**唯一数据源**（它承载的能力声明、分发边界、宿主入口仍然无可替代），新增 `devtools/` 下生成器，把它编译成各客户端 manifest。纳入 `sync_version.py` 的规则表校验一致性。

**预期收益**：既不丢掉现有的强约束，又能被生态识别。**不要二选一** —— 这是本次对标里最容易被误判的一点。

#### P1-6 SKILL.md 瘦身，回归"路由与触发"

**做法**：把"执行规则""质量评审必做步骤""输出要求""质量门禁""交付深度策略""知识库消费规则"等章节下沉到 `references/`，SKILL.md 只保留：能力摘要（对齐 manifest 的 7 项）、触发条件、四种执行模式的一句话索引、资源路由表、最小交付协议。

**目标**：正文从 6,045 字符压缩到 ≤ 3,000 字符。

**预期收益**：常驻上下文更干净、触发精度更高（元数据不被长正文稀释）、符合标准的渐进披露模型。同时降低 `capability_audit` 对少数 token 的隐式依赖（相应 token 需迁到 `references/` 并同步审计规则）。

### P2 — 长期增益

| 编号 | 优化点 | 预期收益 |
|---|---|---|
| P2-7 | 发布到 skills.sh，并在 CI 校验 `skills-lock.json` 与源一致 | 进入 9,500+ skills 的注册表分发；可复现安装 |
| P2-8 | 引入 `agnix`（或对齐其规则集）做 SKILL.md / hooks / MCP 的语法 lint | 与自研语义审计互补；生态规则外溢时能提前发现 |
| P2-9 | 给 `sync_version` / `package_skill` 补单测（目前零覆盖） | 版本与打包这两个最关键路径有回归保护 |
| P2-10 | 收口 `v2.2.0` changelog；引入 `.version-bump.json` 式发版脚本 | 发版流程闭环，历史可追溯 |
| P2-11 | 增加 `.agents/skills/` 兼容层 | 复用 skills CLI 的通用目录约定，降低多客户端落盘成本 |

---

## 5. 不建议做的事

对标中最容易走偏的地方，这里明确列出：

1. **不要为了"符合标准"删掉 `skill.manifest.json`。** 它是本项目最强的资产（能力矩阵 + 分发边界 + 宿主入口 + 版本源），生态里的插件清单远没有这么强的约束力。正确做法是让它**成为 plugin.json 的生成源**。
2. **不要盲目删除 `adapters/`。** Agent Plugins 只覆盖"可移植的地板"，客户端特有的 hooks、权限、UX 仍需各自声明（反域名命名空间正是为此设计的）。适配层应从"整树复制"降级为"manifest 声明"，而不是消失。
3. **不要把六阶段流水线压进 SKILL.md。** 生态里的"轻 skill"是因为它们解决单点问题；本项目的方法论深度是差异化优势，正确动作是**下沉到 `references/` 并用路由指向**，而不是删减。
4. **不要为对齐 `skills/<name>/` 布局而做一次性大重构。** 先用 `skills: ["."]` 拿到原生安装能力（P0-1），等 P1-4 收敛单一树时再自然迁移。
5. **不要把 AGENTS.md 写成项目宪法的副本。** 它每会话注入，长文件会实测降低 agent 表现。短、准、只放不可推断项。

---

## 6. 落地顺序建议

```
P0-1 插件清单  ─┐
P0-2 根 AGENTS  ├─► 可并行，互不冲突，建议同批提交
P0-3 CI        ─┘
        │
        ▼
P1-5 manifest→plugin 生成器   （先固化数据源角色）
        │
        ▼
P1-4 单一树 + 多 manifest     （依赖 P1-5，收益最大、风险最高）
        │
        ▼
P1-6 SKILL.md 瘦身            （与 P1-4 无耦合，可独立进行）
        │
        ▼
P2 项按需推进
```

---

## 7. 参考来源

| 主题 | 来源 |
|---|---|
| Agent Skills 标准 | <https://agentskills.io/specification> ｜ <https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills> |
| Agent Plugins v1.0.0 | <https://agent-plugins.org> ｜ <https://github.com/agentplugins/agent-plugins-spec> |
| Claude Code 插件与市场 | <https://code.claude.com/docs/en/plugins> ｜ <https://code.claude.com/docs/en/plugin-marketplaces> |
| AGENTS.md | <https://agents.md> ｜ <https://github.com/agentsmd/agents.md> |
| 官方 Skill 仓库与模板 | <https://github.com/anthropics/skills> |
| 多客户端实践样本 | <https://github.com/obra/superpowers> |
| skills CLI 与注册表 | <https://skills.sh>（`npx skills`） |
| agent 配置 linter | `agnix`（社区实现，156 条规则） |
