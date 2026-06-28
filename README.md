# 🧪 Test Generator · AI 驱动的测试用例生成 Skill

<p align="center">
  <strong>🔬 让大模型真正"写出能跑"的测试用例</strong><br>
  <em>基于 MBT 方法论的六阶段智能流水线 · 一键激活到 8 个主流 AI 宿主</em>
</p>

<p align="center">
  <a href="#-why"><strong>Why</strong></a> ·
  <a href="#-what"><strong>What</strong></a> ·
  <a href="#-how"><strong>How</strong></a> ·
  <a href="#-特性">特性</a> ·
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-架构">架构</a> ·
  <a href="#-使用指南">使用指南</a> ·
  <a href="#-多宿主支持">多宿主</a> ·
  <a href="#-质量保障">质量保障</a>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@wychmod-cn/testcase-generator-skill"><img src="https://img.shields.io/npm/v/@wychmod-cn/testcase-generator-skill?label=npm&color=cb3837" alt="npm"></a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/MBT-ISO%2FIEC%2029119-purple.svg" alt="MBT">
  <img src="https://img.shields.io/badge/AI--Hosts-8-orange.svg" alt="AI Hosts">
  <a href="https://github.com/wychmod/test-generator/stargazers"><img src="https://img.shields.io/github/stars/wychmod/test-generator?style=social" alt="Stars"></a>
</p>

<p align="center">
  <strong>GitHub Topics:</strong>
  <code>testing</code> ·
  <code>testcase-generation</code> ·
  <code>mbt</code> ·
  <code>model-based-testing</code> ·
  <code>test-automation</code> ·
  <code>quality-assurance</code> ·
  <code>automation</code> ·
  <code>claude-code</code> ·
  <code>codex</code> ·
  <code>ai-driven</code> ·
  <code>testing-tool</code> ·
  <code>skill</code>
</p>

---

## 🤔 Why · 为什么会有这个项目

测试工程师每天面临三个绕不开的痛点：

| 痛点 | 现状 | 期望 |
|---|---|---|
| **用例产出慢** | 4 小时/功能,迭代跟不上 | **15 分钟内一版能用** |
| **AI 生成用例不敢用** | 幻觉严重、覆盖率不可控 | **结构化、可追溯、可评审** |
| **多工具协作成本高** | Claude / Codex / Qoder / Cursor 各玩各的 | **一套 Skill 8 个宿主通用** |

**Test Generator 把"AI 生成测试用例"从 demo 拉到工程级**——不是 prompt 调优的玩具,
是基于 ISTQB MBT 方法论,带质量门禁、双向追溯、反馈闭环的生产级方案。

---

## 🎯 What · 它是什么

**Test Generator** 是一个面向 AI Agent 的 **Skill 元件库 + 六阶段流水线框架**。

它做的事情可以一句话概括:

> 把"一段需求描述 / 一份 PRD / 一份 API 规范 / 一段代码"作为输入,
> 通过 **六阶段流水线(输入预处理 → 需求预处理 → 代码分析 → 领域建模 → MBT 设计 → 用例生成)**,
> 输出 **结构化、可评审、可追溯**的测试用例。

它**不是一个 CLI 工具**,而是一个 **Skill 包**——安装后会被注入到你正在使用的 AI 宿主
(Claude Code / Codex / Qoder / CodeBuddy / Cursor / Windsurf / OpenClaw / Trae)中,
让宿主 AI 按照这套方法论帮你生成用例。

---

## ⚙️ How · 它怎么工作

```text
用户输入 → [输入预处理] → [六阶段流水线] → [输出层]
              ↓                ↓               ↓
         格式规范化     P0→1→2→3→4→5      多阶段文档产物
         质量评分         ↓               追溯矩阵
         缺口识别      [Quality Gate]    反馈闭环
```

每一阶段都有独立 prompt + 质量门禁 + 双向追溯,而不是把一切都丢给大模型自由发挥。

📖 **架构详解见** [docs/architecture/](./docs/architecture/) | **六阶段产出物详解** [resources/output_artifacts.md](./resources/output_artifacts.md)

---

## ✨ 特性

### 🏗️ 生产级架构
- **六阶段流水线**:输入预处理 → 需求预处理 → 代码分析 → 领域建模 → MBT 设计 → 用例生成
- **质量门禁系统**:关键阶段完成后可进行质量检查与一致性校验
- **双向可追溯**:需求 ↔ 测试用例之间可建立追溯矩阵
- **反馈闭环**:支持根据执行结果、漏测场景和规则修正持续优化产物

### 🧠 智能 AI 能力
- **多格式输入**:支持需求文档、PRD、API 规范、源代码、自然语言描述等输入
- **输入质量预处理**:在正式分析前先做规范化、质量评分与缺口识别
- **歧义与风险识别**:帮助发现模糊需求、边界遗漏、潜在冲突与测试盲区
- **代码与契约辅助分析**:可从实现细节、接口契约和数据流中反推测试点
- **本地知识库检索**:支持术语表、项目规范、历史用例等 Markdown 知识条目的触发式 BM25 检索,并在用例追溯中保留 `KB:` 引用
- **增量代码扫描**:支持从 unified diff 中提取新增代码行,辅助判断 PRD 对齐情况并识别硬编码密钥、裸 `except`、动态执行、SQL 拼接等风险信号

### 📊 专业测试工程
- **MBT 方法论**:围绕领域模型、状态迁移、覆盖准则组织测试设计(对齐 ISO/IEC/IEEE 29119-3:2021)
- **边界值 + 等价类**:系统化支持 BVA / EP / 决策表等分析方法
- **状态机推导**:自动构建状态转换规格与路径集合
- **参数空间优化**:支持 Pairwise、组合裁剪与风险导向覆盖
- **结构化输出**:生成便于评审、追踪和复用的测试设计产物

### 🎯 多场景覆盖
- **正向 / 负向**:Happy Path 与异常场景结合
- **接口 / 领域 / 状态**:适用于 API、业务流程、状态型系统测试
- **回归 / 审计 / 标准化**:适合测试补齐、测试审计、统一格式化输出
- **自动化适配**:可为后续 Pytest / Playwright / Cucumber 等自动化落地提供基础骨架
- **多宿主一键激活**:`test-generator activate all` 可一次性激活 Claude / Codex / Qoder / OpenClaw / Trae / CodeBuddy / Cursor / Windsurf

### 📚 v2.2.0 新增能力
- **知识库辅助层**:新增 `knowledge/`,可维护项目术语、规范、历史用例和合规规则;支持 `build_index.py` 构建本地索引、`search.py` 检索命中片段、`ingest.py` 接入用户自定义 LLM 命令录入知识
- **Phase 2 增量分析辅助**:新增 `scripts/incremental_code_scan.py`,可对 diff / patch 做新增行解析、PRD 需求 ID 匹配和潜在缺陷雷达输出
- **文档中心**:新增 `docs/`,集中维护架构、开发、发布、质量与 changelog 文档,根目录只保留分发必需入口
- **激活体验优化**:npm CLI 支持 `activate all`,并保留 `activate <environment>`、`-g`、`--dry-run` 等单平台能力

---

## 👥 Who is this for · 谁适合用

✅ **强烈推荐使用**

- 🧪 **测试工程师 / QA Lead** — 想把 AI 用到测试设计,但担心幻觉和不可控
- 💻 **全栈 / 后端开发** — 写完代码想快速补一组高质量测试,不想从零设计
- 🤖 **AI Agent 实践者** — 用 Claude Code / Codex / Cursor 等做开发,想让 AI 按规范走流程
- 📋 **PM / 业务分析师** — 想在需求阶段就识别模糊点和漏测风险

⚠️ **谨慎使用**

- 完全没有测试基础概念的纯小白(本 Skill 假设使用者懂基本测试术语)
- 不接受 AI 辅助、纯手写党(本项目就是为 AI 协作设计的)

---

## 📦 安装

```bash
# 方式一:Node.js/npm 安装并激活到宿主环境(最推荐)
npm i @wychmod-cn/testcase-generator-skill
test-generator activate all

# 如需只激活单个平台,也可以使用:
test-generator activate claude
test-generator activate codex
test-generator activate qoder
test-generator activate openclaw
test-generator activate trae
test-generator activate codebuddy
test-generator activate cursor
test-generator activate windsurf

# 方式二:Vercel skills CLI
npm install -g skills
npx skills add https://github.com/wychmod/test-generator -y

# 方式三:本地 ZIP 安装
npx skills add ./testcase-generator.zip

# 方式四:手动安装
# 通过已打包的 Skill 文件安装
# 在支持 .skill 的宿主平台中导入
./testcase-generator.skill
./testcase-generator.zip
```

> 最推荐使用 `npm i @wychmod-cn/testcase-generator-skill` 安装;仅在无法使用 npm 时再选择 `testcase-generator.skill` 或 `testcase-generator.zip`。
> npm 方式不会改变 `.skill` / `.zip` 产物,只是提供 `test-generator activate all` 和 `test-generator activate <environment>` 将 Skill 运行时文件复制到对应宿主目录。

---

## 🚀 快速开始

### 基本用法

```bash
# 最简方式 — 一句话描述
/testcase-generator 为用户登录功能生成测试用例

# 基于文件
/testcase-generator ./requirements/order-system.md

# 指定选项
/testcase-generator --format=gherkin --priority=P0,P1 支付模块完整测试

# 完整配置
/testcase-generator --config=./config/example-config.json 订单管理系统全量测试

# 参考本地知识库
/testcase-generator 参考知识库,按项目规范生成登录密码强度测试用例

# 针对代码变更做回归设计
/testcase-generator 根据本次 diff 和 PRD 生成优惠券模块回归测试
```

### 适合什么输入

你可以直接提供以下任一类输入:

- 一段自然语言需求描述
- PRD / 需求文档路径
- 模块名、子系统名、业务流程名
- 接口说明、字段定义、状态流转规则
- 源代码或代码目录

输入越完整,生成结果通常越稳定;但即使输入不完整,也会先尝试识别缺口、补齐上下文并提示风险。

---

## 🌐 多宿主支持

v2.2.0 起,本 Skill 支持一键激活到 **8 个主流 AI 宿主**:

| 宿主 | 适配方式 | 激活命令 |
|---|---|---|
| **Claude Code** | 完整适配 | `test-generator activate claude` |
| **Codex** | 完整适配 | `test-generator activate codex` |
| **Qoder** | 完整适配 | `test-generator activate qoder` |
| **CodeBuddy**(腾讯云 AI 代码助手) | 完整适配 | `test-generator activate codebuddy` |
| **Cursor** | 软适配(`.cursorrules`) | `test-generator activate cursor` |
| **Windsurf / Antigravity** | 软适配(`.windsurfrules`) | `test-generator activate windsurf` |
| **OpenClaw** | 兼容适配 | `test-generator activate openclaw` |
| **Trae** | 完整适配 | `test-generator activate trae` |

> 想全部激活?一行命令搞定:
>
> ```bash
> test-generator activate all
> ```

---

## 🏛️ 架构

### 整体流程

```text
用户输入 → [输入预处理] → [六阶段流水线] → [输出层]
              ↓                ↓               ↓
         格式规范化     P0→1→2→3→4→5      多阶段文档产物
         质量评分         ↓               追溯矩阵
         缺口识别      [Quality Gate]    反馈闭环
```

### 六阶段详解

| 阶段 | 名称 | 核心产出 | 关键能力 |
|------|------|---------|---------|
| **Phase 0** | 输入预处理 | 输入质量评估 + 规范化建议 | 缺口识别、输入增强、质量评分 |
| **Phase 1** | 需求预处理 | 结构化需求 + 可测需求 + 边界条件 | 需求抽取、冲突检测、NFR 分析 |
| **Phase 2** | 代码分析 | 代码结构 + 数据流 + 缺陷雷达 | 静态分析、契约推导、并发与风险识别 |
| **Phase 3** | 领域建模 | 领域模型 + 状态机 + 参数空间 | 实体建模、状态完备性验证、组合优化 |
| **Phase 4** | MBT 设计 | 测试模型 + 覆盖准则 + 路径集 | 风险导向设计、覆盖裁剪、错误猜测 |
| **Phase 5** | 用例生成 | 用例集 + 套件摘要 + 追溯矩阵 | 结构化用例生成、去重、产物汇总 |

---

## 📖 使用指南

### 适用场景

| 场景 | 推荐命令 | 配置建议 |
|------|---------|---------|
| 新功能首次测试 | `/testcase-generator [功能描述]` | `--depth=full` |
| 迭代回归测试 | `/testcase-generator --format=json [变更描述]` | `--priority=P0,P1` |
| API 契约测试 | `/testcase-generator openapi.yaml` | 重点查看契约与边界分析 |
| 状态流专项分析 | `/testcase-generator [业务流程]` | 重点查看 Phase 3 / Phase 4 |
| 合规交付 | `/testcase-generator [需求文档] --traceability=full` | 确保追溯矩阵完整 |
| 知识库辅助生成 | `/testcase-generator 参考知识库 [功能描述]` | 先用 `knowledge/scripts/search.py` 检索相关规范或历史用例 |
| 增量回归分析 | `/testcase-generator [diff/patch + PRD]` | 可先运行 `scripts/incremental_code_scan.py` 获取新增行、需求对齐与风险信号 |

### 输出格式选择

| 格式 | 命令参数 | 适用场景 |
|------|---------|---------|
| Markdown(默认) | `--format=markdown` | 正式文档交付、人工评审 |
| Gherkin/BDD | `--format=gherkin` | 敏捷团队、Cucumber/Behave |
| JSON | `--format=json` | CI/CD 集成、工具链处理 |

### 测试深度选择

| 深度 | 参数 | 用例数量(估) | 用时(估) | 适用时机 |
|------|------|-------------|---------|---------|
| Smoke | `--depth=smoke` | 5-15 | 5-10 min | 每次 CI 构建 |
| Standard | `--depth=standard` | 30-100 | 20-60 min | 每日/每周构建 |
| Full | `--depth=full` | 100-300 | 1-3 hr | 版本发布前 |
| Exploratory | `--depth=exploratory` | 50-150 | 1-2 hr | 安全/性能专项 |

---

## 📦 输出产物

典型输出会覆盖多个阶段,常见包括:

```text
test-output/
├── phase1/
│   ├── 01_requirements_summary.md
│   ├── 02_testable_requirements.md
│   └── 03_boundary_conditions.md
├── phase2/
│   ├── 01_code_structure.md
│   ├── 02_data_flow_analysis.md
│   └── 03_defect_radar.md
├── phase3/
│   ├── 01_business_domain_model.md
│   ├── 02_state_machine_spec.md
│   └── 03_test_parameter_space.md
├── phase4/
│   ├── 01_test_model_specification.md
│   ├── 02_state_transition_graph.md
│   └── 03_coverage_criteria.md
├── phase5/
│   ├── 01_testcase_collection.md
│   ├── 02_test_suite_summary.md
│   └── 03_traceability_matrix.md
└── quality_report.md
```

更完整的阶段产物说明可参考:[`resources/output_artifacts.md`](./resources/output_artifacts.md)。

---

## 📚 知识库

v2.2.0 新增本地知识库辅助层,用于保存生成测试用例时会反复参考的稳定信息,例如项目术语、命名规范、错误码约定、历史用例和合规规则。

```bash
# 首次或修改 knowledge/sources 后重建索引
python knowledge/scripts/build_index.py --rebuild

# 检索规范、术语或历史用例
python knowledge/scripts/search.py "密码强度"
python knowledge/scripts/search.py "登录失败" --source historical-cases
python knowledge/scripts/search.py "支付回调" --json --top-k 5
```

录入新知识时,推荐复制 `knowledge/llm-ingest-template.md` 给大模型,让模型输出可索引 Markdown,再保存到 `knowledge/sources/<slug>.md`。使用知识库生成用例时,命令中写明"参考知识库""按规范""参考历史用例"即可;最终用例应在追溯引用中保留 `KB:` 来源。

---

## 🔎 增量代码扫描

v2.2.0 新增 `scripts/incremental_code_scan.py`,用于 Phase 2 代码分析前的轻量辅助。它会解析 unified diff,提取新增行,尝试按 token overlap 匹配 PRD 需求,并标记常见高风险代码模式。

```bash
python scripts/incremental_code_scan.py --diff-file changes.patch --prd requirements/coupon.md
python scripts/incremental_code_scan.py --diff-file changes.patch --prd requirements/coupon.md --format markdown
```

该脚本不是完整静态分析器,适合在 PR / patch 语境中快速给出"本次变更影响了什么、可能漏测什么、哪些新增行需要重点回归"的结构化上下文。

---

## ⚙️ 配置

### 命令行参数速查

| 参数 | 缩写 | 说明 | 默认值 |
|------|-----|------|--------|
| `--format` | `-f` | 输出格式 | markdown |
| `--priority` | `-p` | 用例优先级过滤 | all |
| `--depth` | `-d` | 测试深度 | standard |
| `--output` | `-o` | 输出目录 | `./test-output/` |
| `--config` | `-c` | 配置文件路径 | 无 |
| `--lang` | `-l` | 输出语言 | auto |

### 配置文件示例

创建配置文件来自定义生成行为:

```json
{
  "project": { "name": "MyProject" },
  "generation": {
    "output_format": "markdown",
    "boundary_analysis": { "method": "robust" },
    "deduplication": { "enabled": true, "similarity_threshold": 0.85 }
  },
  "coverage": {
    "requirements_coverage_target": 100,
    "path_coverage_target": "critical+normal"
  },
  "quality": {
    "enable_gate_check": true,
    "strict_mode": false,
    "hallucination_detection": true
  }
}
```

详细配置见:

- [`config/example-config.json`](./config/example-config.json)
- [`config/testcase-config-schema.json`](./config/testcase-config-schema.json)

---

## 🛡️ 质量保障

### 质量门禁

关键阶段可结合质量检查机制进行审计,重点关注:

| 阶段 | 主要检查维度 | 参考阈值 |
|------|------------|---------|
| P0 输入预处理 | 输入完整性、格式规范性、缺口识别质量 | ≥ 80 分 |
| P1 需求预处理 | 完整性、准确性、可测试性、一致性 | ≥ 80 分 |
| P2 代码分析 | 分析范围、数据流、缺陷依据、需求对齐 | ≥ 80 分 |
| P3 领域建模 | 模型质量、状态机完备性、跨阶段一致性 | ≥ 85 分 |
| P4 MBT 设计 | 覆盖准则合理性、可操作性、设计完整性 | ≥ 85 分 |
| P5 用例生成 | 覆盖完整性、用例质量、去重效果、规范性 | ≥ 90 分 |

### 一致性审计

可使用开发审计脚本检查能力矩阵是否落地:

```bash
python devtools/capability_audit.py
python devtools/capability_audit.py --format json
```

审计会检查:

- `SKILL.md` / `README.md` / `skill.manifest.json` 的版本与能力声明是否一致
- Prompt、模板、资源文件是否齐全
- Schema 是否有效
- 示例配置是否能被 Schema 验证
- 反馈闭环与阶段产物资源是否存在
- 分发层关键文件是否齐全

---

## 📁 项目结构

```text
testcase-generator/
├── SKILL.md                              # 🔑 Skill 主文件(核心入口)
├── README.md                             # 📖 本文件
├── DISTRIBUTION.md                       # 📦 分发边界与发布检查项
├── HOST_COMPATIBILITY.md                 # 🧩 宿主兼容性说明
├── skill.manifest.json                   # 🗂️ 分发元数据与入包规则
├── run_package.bat                       # 🛠️ Windows 打包入口
│
├── adapters/                             # 🔌 多宿主适配入口
│   ├── claude/                          #   Claude / Anthropic 类宿主
│   ├── codex/                           #   Codex / 工程 CLI 类宿主
│   ├── codebuddy/                       #   CodeBuddy / 腾讯云 AI 代码助手
│   ├── cursor/                          #   Cursor (Anysphere) 软适配
│   ├── openclaw/                        #   OpenClaw / 兼容型宿主
│   ├── qoder/                           #   Qoder / IDE 集成类宿主
│   └── windsurf/                        #   Windsurf / Antigravity 软适配
│
├── config/                               # ⚙️ 配置文件
│   ├── example-config.json               #   配置示例
│   └── testcase-config-schema.json       #   JSON Schema 校验定义
│
├── prompts/                              # 📝 各阶段提示词(AI 执行指令)
│   ├── phase0_input_preprocessing_prompt.md
│   ├── phase1_requirements_prompt.md
│   ├── phase2_code_analysis_prompt.md
│   ├── phase3_domain_analysis_prompt.md
│   ├── phase4_mbt_design_prompt.md
│   └── phase5_testcase_generation_prompt.md
│
├── scripts/                              # 🐍 运行时辅助脚本
│   ├── prd_reader.py                     #   PRD / Markdown / PDF 读取辅助
│   └── incremental_code_scan.py          #   diff 增量代码行 + PRD 符合性 + 潜在 bug 扫描
│
├── knowledge/                            # 📚 本地知识库(v2.2.0)
│   ├── README.md                         #   知识库使用说明
│   ├── llm-ingest-template.md            #   大模型知识录入模板
│   ├── sources/                          #   可检索 Markdown 知识条目
│   └── scripts/                          #   build_index / search / ingest 工具
│
├── docs/                                 # 🧭 内部文档中心
│   ├── architecture/                     #   架构设计
│   ├── development/                      #   开发指南
│   ├── operations/                       #   打包与发布
│   └── quality/                          #   质量与测试计划
│
├── devtools/                             # 🧪 开发与发布工具
│   ├── capability_audit.py               #   能力矩阵与资产一致性审计
│   ├── skill_quality_audit.py            #   Skill 标准字段与质量门禁审计
│   └── package_skill.py                  #   Skill 打包脚本
│
├── templates/                            # 📋 输出模板(产物格式规范)
│   ├── requirements_template.md
│   ├── state_diagram_template.md
│   └── testcase_template.md
│
├── resources/                            # 📚 参考资源
│   ├── feedback_template.md              #   反馈闭环模板
│   ├── output_artifacts.md               #   阶段产物说明
│   ├── quality_checklist.md              #   质量检查指南
│   └── testcase_formats.md               #   测试用例格式参考
│
└── test-output/                          # 🧾 本地测试输出示例(不参与分发)
```

---

## 🔄 版本历史

### v2.2.0 (2026-06)
- 新增 `knowledge/` 本地知识库:支持项目术语、项目规范、历史用例、API 速查和合规规则的 Markdown 化管理
- 新增 BM25 本地检索工具:`knowledge/scripts/build_index.py`、`knowledge/scripts/search.py`,支持触发词检索、source 过滤、JSON 输出和 Top-K 命中片段
- 新增知识录入链路:`knowledge/llm-ingest-template.md` 支持手动喂给大模型,`knowledge/scripts/ingest.py` 支持通过用户配置的 LLM 命令自动写入 `knowledge/sources/`
- 新增 `scripts/incremental_code_scan.py`:支持 diff 新增行解析、PRD 需求 ID / token 对齐、潜在 bug 规则扫描和 Markdown / JSON 输出
- 新增 `docs/` 文档中心,补充架构、开发、发布、质量与 changelog 文档入口
- npm 激活命令支持 `test-generator activate all`,可一次性激活全部支持宿主;`--target` 保持为单平台激活专用

### v2.1.0 (2026-04)
- 新增 **Phase 0 输入预处理**,从五阶段升级为六阶段流水线
- 引入 `skill.manifest.json` 作为分发元数据与入包边界定义
- 新增 `DISTRIBUTION.md` 与 `HOST_COMPATIBILITY.md`,补充分发与兼容性说明
- 增加 `resources/output_artifacts.md`,承接阶段产物的详细定义
- 打包与审计工具迁移至 `devtools/`,区分运行时资产与开发工具
- 增加 `adapters/` 目录,为多宿主入口做统一收口
- 扩展适配器生态:
  - 新增 `adapters/codebuddy/SKILL.md`(腾讯云 CodeBuddy 完整适配)
  - 新增 `adapters/cursor/cursorrules.md`(Anysphere Cursor 软适配,激活时复制为 `.cursorrules`)
  - 新增 `adapters/windsurf/windsurfrules.md`(Codeium / Google Windsurf / Antigravity 软适配,激活时复制为 `.windsurfrules`)
  - `lib/activation.js` 支持环境从 5 个扩展到 8 个(`claude` / `qoder` / `codex` / `openclaw` / `trae` / `codebuddy` / `cursor` / `windsurf`)

### v2.0.0 (2026-04-04)
- 五阶段流水线架构 + 质量门禁系统
- 完整配置系统与模板/资源体系
- 歧义、冲突、幻觉等检测机制
- 双向追溯矩阵与测试用例去重能力

### v1.1.0
- 增加网络调研能力
- 增加模板系统和资源文件

### v1.0.0
- 五阶段基础流程

---

## 📄 License

MIT License © 2024-2026 Test Generator Team

---

## 👤 作者

**韦语轩 (wychmod)** — 长期关注 AI Agent 在企业研发流程中的工程化落地。

- 🌐 个人博客:[https://wychmod.github.io](https://wychmod.github.io)
- 📧 联系邮箱:`wychmod@foxmail.com`
- 💻 GitHub:[@wychmod](https://github.com/wychmod)
- 📦 NPM:[@wychmod-cn](https://www.npmjs.com/~wychmod-cn)

---

## 🌟 相关项目

如果你对 AI 工具链感兴趣,以下项目可能也对你有帮助:

| 项目 | 简介 | Star |
|---|---|---|
| [**openai-gateway**](https://github.com/wychmod/openai-gateway) | ChatGPT 网关服务 · 多 API Key 负载均衡 · 飞书 OAuth | ⭐ 38 |
| [**agent-v**](https://github.com/wychmod/agent-v) | AI Agent 实验场 · Tool-use / 多 Agent / RAG | — |
| [**mini-spring**](https://github.com/wychmod/mini-spring) | 手写 Spring 源码学习项目 | ⭐ 23 |
| [**db-router-springboot-starter**](https://github.com/wychmod/db-router-springboot-starter) | 自研分库分表 Spring Boot Starter | ⭐ 2 |
| [**wychmod.github.io**](https://github.com/wychmod/wychmod.github.io) | 个人知识站 · 300+ 篇技术笔记 | ⭐ 3 |

---

## 🤝 贡献

我们欢迎任何形式的贡献:

- 🐛 **提 Issue** — bug 报告 / 功能建议 / 文档改进
- 🔀 **提 PR** — 代码 / 文档 / 测试 / 适配新 AI 宿主
- 💬 **Discussion** — 分享你的用例生成场景、最佳实践、踩坑经验
- ⭐ **Star** — 你的 Star 是这个项目持续迭代的最大动力

详细贡献指南见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

---

## 🙏 致谢

- **ISTQB** — 国际软件测试认证委员会,MBT 标准方法论
- **ISO/IEC/IEEE 29119-3:2021** — 当前测试文档标准;IEEE 829 仅作为历史兼容参考
- **INCOSE** — 国际系统工程学会,需求工程实践
- **OWASP** — 开放 Web 应用安全项目,安全测试指南
- **所有贡献者** — 感谢每一位提交 Issue、PR 和讨论的同行 🙏

---

<p align="center">
  <sub>Built with ❤️ by Test Generator Team · 让 AI 真正写出能跑、能用、能信的测试用例</sub>
</p>

<p align="center">
  <a href="#-why"><strong>↑ 回到顶部</strong></a> ·
  <a href="https://github.com/wychmod/test-generator"><strong>⭐ Star 这个项目</strong></a>
</p>
