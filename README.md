# TestCase Generator Skill v2.1.0

<!--
GitHub Topics: testing testcase-generation mbt model-based-testing
test-automation quality-assurance automation claude-code skill ai-driven testing-tool
-->

<p align="center">
  <strong>🔬 AI 驱动的生产级测试用例生成器</strong><br>
  <em>基于 MBT（Model-Based Testing）方法论的六阶段智能流水线</em>
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#安装">安装</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#架构">架构</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#输出产物">输出产物</a> •
  <a href="#配置">配置</a> •
  <a href="#质量保障">质量保障</a> •
  <a href="#项目结构">项目结构</a>
</p>

---

## 📦 安装

```bash
# 方式一：Vercel skills CLI（推荐）
npm install -g skills
npx skills add https://github.com/wychmod/test-generator -y

# 方式二：本地 ZIP 安装
npx skills add ./testcase-generator.zip

# 方式三：手动安装
# 通过已打包的 Skill 文件安装（推荐）
# 在支持 .skill 的宿主平台中导入
./testcase-generator.skill
./testcase-generator.zip
```

> 推荐优先使用 `testcase-generator.skill`；仅在宿主平台暂不支持 `.skill` 时再使用 `testcase-generator.zip`。

---

## ✨ 特性

### 🏗️ 生产级架构
- **六阶段流水线**：输入预处理 → 需求预处理 → 代码分析 → 领域建模 → MBT 设计 → 用例生成
- **质量门禁系统**：关键阶段完成后可进行质量检查与一致性校验
- **双向可追溯**：需求 ↔ 测试用例之间可建立追溯矩阵
- **反馈闭环**：支持根据执行结果、漏测场景和规则修正持续优化产物

### 🧠 智能 AI 能力
- **多格式输入**：支持需求文档、PRD、API 规范、源代码、自然语言描述等输入
- **输入质量预处理**：在正式分析前先做规范化、质量评分与缺口识别
- **歧义与风险识别**：帮助发现模糊需求、边界遗漏、潜在冲突与测试盲区
- **代码与契约辅助分析**：可从实现细节、接口契约和数据流中反推测试点

### 📊 专业测试工程
- **MBT 方法论**：围绕领域模型、状态迁移、覆盖准则组织测试设计
- **边界值 + 等价类**：系统化支持 BVA / EP / 决策表等分析方法
- **状态机推导**：自动构建状态转换规格与路径集合
- **参数空间优化**：支持 Pairwise、组合裁剪与风险导向覆盖
- **结构化输出**：生成便于评审、追踪和复用的测试设计产物

### 🎯 多场景覆盖
- **正向 / 负向**：Happy Path 与异常场景结合
- **接口 / 领域 / 状态**：适用于 API、业务流程、状态型系统测试
- **回归 / 审计 / 标准化**：适合测试补齐、测试审计、统一格式化输出
- **自动化适配**：可为后续 Pytest / Playwright / Cucumber 等自动化落地提供基础骨架

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
```

### 适合什么输入

你可以直接提供以下任一类输入：

- 一段自然语言需求描述
- PRD / 需求文档路径
- 模块名、子系统名、业务流程名
- 接口说明、字段定义、状态流转规则
- 源代码或代码目录

输入越完整，生成结果通常越稳定；但即使输入不完整，也会先尝试识别缺口、补齐上下文并提示风险。

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

### 输出格式选择

| 格式 | 命令参数 | 适用场景 |
|------|---------|---------|
| Markdown (默认) | `--format=markdown` | 正式文档交付、人工评审 |
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

典型输出会覆盖多个阶段，常见包括：

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

更完整的阶段产物说明可参考：`resources/output_artifacts.md`。

---

## ⚙️ 配置

### 命令行参数速查

| 参数 | 缩写 | 说明 | 默认值 |
|------|-----|------|--------|
| `--format` | `-f` | 输出格式 | markdown |
| `--priority` | `-p` | 用例优先级过滤 | all |
| `--depth` | `-d` | 测试深度 | standard |
| `--output` | `-o` | 输出目录 | ./test-output/ |
| `--config` | `-c` | 配置文件路径 | 无 |
| `--lang` | `-l` | 输出语言 | auto |

### 配置文件示例

创建配置文件来自定义生成行为：

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

详细配置见：

- `config/example-config.json`
- `config/testcase-config-schema.json`

---

## 🛡️ 质量保障

### 质量门禁

关键阶段可结合质量检查机制进行审计，重点关注：

| 阶段 | 主要检查维度 | 参考阈值 |
|------|------------|---------|
| P0 输入预处理 | 输入完整性、格式规范性、缺口识别质量 | ≥ 80 分 |
| P1 需求预处理 | 完整性、准确性、可测试性、一致性 | ≥ 80 分 |
| P2 代码分析 | 分析范围、数据流、缺陷依据、需求对齐 | ≥ 80 分 |
| P3 领域建模 | 模型质量、状态机完备性、跨阶段一致性 | ≥ 85 分 |
| P4 MBT 设计 | 覆盖准则合理性、可操作性、设计完整性 | ≥ 85 分 |
| P5 用例生成 | 覆盖完整性、用例质量、去重效果、规范性 | ≥ 90 分 |

### 一致性审计

可使用开发审计脚本检查能力矩阵是否落地：

```bash
python devtools/capability_audit.py
python devtools/capability_audit.py --format json
```

审计会检查：

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
├── SKILL.md                              # 🔑 Skill 主文件（核心入口）
├── README.md                             # 📖 本文件
├── DISTRIBUTION.md                       # 📦 分发边界与发布检查项
├── HOST_COMPATIBILITY.md                 # 🧩 宿主兼容性说明
├── skill.manifest.json                   # 🗂️ 分发元数据与入包规则
├── run_package.bat                       # 🛠️ Windows 打包入口
│
├── adapters/                             # 🔌 多宿主适配入口
│   ├── claude/
│   ├── codex/
│   ├── openclaw/
│   └── qoder/
│
├── config/                               # ⚙️ 配置文件
│   ├── example-config.json               #   配置示例
│   └── testcase-config-schema.json       #   JSON Schema 校验定义
│
├── prompts/                              # 📝 各阶段提示词（AI 执行指令）
│   ├── phase0_input_preprocessing_prompt.md
│   ├── phase1_requirements_prompt.md
│   ├── phase2_code_analysis_prompt.md
│   ├── phase3_domain_analysis_prompt.md
│   ├── phase4_mbt_design_prompt.md
│   └── phase5_testcase_generation_prompt.md
│
├── scripts/                              # 🐍 运行时辅助脚本
│   └── prd_reader.py                     #   PRD / Markdown / PDF 读取辅助
│
├── devtools/                             # 🧪 开发与发布工具
│   ├── capability_audit.py               #   能力矩阵与资产一致性审计
│   └── package_skill.py                  #   Skill 打包脚本
│
├── templates/                            # 📋 输出模板（产物格式规范）
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
└── test-output/                          # 🧾 本地测试输出示例（不参与分发）
```

---

## 🔄 版本历史

### v2.1.0 (2026-04)
- 新增 **Phase 0 输入预处理**，从五阶段升级为六阶段流水线
- 引入 `skill.manifest.json` 作为分发元数据与入包边界定义
- 新增 `DISTRIBUTION.md` 与 `HOST_COMPATIBILITY.md`，补充分发与兼容性说明
- 增加 `resources/output_artifacts.md`，承接阶段产物的详细定义
- 打包与审计工具迁移至 `devtools/`，区分运行时资产与开发工具
- 增加 `adapters/` 目录，为多宿主入口做统一收口

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

## 🙏 致谢

- **ISTQB**: 国际软件测试认证委员会 — MBT 标准方法论
- **IEEE 829**: 软件测试文档标准
- **INCOSE**: 国际系统工程学会 — 需求工程实践
- **OWASP**: 开放 Web 应用安全项目 — 安全测试指南

---

<p align="center">
  <sub>Built with ❤️ by testcase-generator v2.1 | 基于 AI 的生产级测试用例生成方案</sub>
</p>
