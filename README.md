# TestCase Generator Skill v2.0

<!--
GitHub Topics: testing testcase-generation mbt model-based-testing
test-automation quality-assurance automation claude-code skill ai-driven testing-tool
-->

<p align="center">
  <strong>🔬 AI 驱动的生产级测试用例生成器</strong><br>
  <em>基于 MBT（Model-Based Testing）方法论的五阶段智能流水线</em>
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#安装">安装</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#架构">架构</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#输出产物">输出产物</a> •
  <a href="#配置">配置</a>
  •
  <a href="#质量保障">质量保障</a>
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
# 下载 ZIP 并解压到对应工具的 skills 目录
# - Claude Code: ~/.claude/skills/<skill-name>/
# - 其他兼容工具: ./.workbuddy/skills/<skill-name>/
```

---

## ✨ 特性

### 🏗️ 生产级架构
- **五阶段流水线**：需求预处理 → 代码分析 → 领域建模 → MBT设计 → 用例生成
- **质量门禁系统**：每阶段完成后自动执行量化质量检查
- **错误恢复机制**：完整的错误分类、检测和自动修复策略
- **双向可追溯**：需求↔用例的完整追溯矩阵

### 🧠 智能 AI 能力
- **多格式输入**：支持需求文档、源代码、API 规范、自然语言等任意输入
- **歧义自动检测**：识别模糊需求并标注 [需确认] 或 [推断]
- **冲突发现**：自动检测需求之间的逻辑矛盾和定义重叠
- **主动知识检索**：基于领域自动搜索最佳实践补充分析

### 📊 专业测试工程
- **MBT 方法论**：遵循 ISTQB Advanced Level Test Analyst 标准
- **边界值 + 等价类**：系统化的 BVA 和 EP 分析
- **状态机推导**：自动构建完整的状态转换图 (Mealy/Moore/Statechart)
- **参数空间优化**：Pairwise / 正交数组 / 全组合策略
- **用例去重**：语法去重 + 语义去重 + 覆盖去重三重过滤

### 🎯 多场景覆盖
- **正向/负向**：Happy Path + 异常场景全覆盖
- **安全专项**：OWASP Top 10 / CWE 缺陷模式匹配
- **性能基线**：响应时间、吞吐量、并发能力指标
- **自动化适配**：Pytest / JUnit / Playwright / Cucumber / Postman 代码骨架

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
/testcase-generator --config=./test-config.json 订单管理系统全量测试
```

### 输出示例

执行后，在 `./test-output/` 目录下生成：

```
test-output/
├── phase1/
│   ├── 01_requirements_summary.md      # 结构化需求摘要 (~200行)
│   ├── 02_testable_requirements.md     # 可测试需求条目化清单
│   └── 03_boundary_conditions.md       # BVA + EP + 决策表
├── phase2/
│   ├── 01_code_structure.md            # 代码架构 + 函数规格表
│   ├── 02_data_flow_analysis.md        # DFD + 数据对象字典
│   └── 03_defect_radar.md              # 潜在缺陷 + 安全检查
├── phase3/
│   ├── 01_business_domain_model.md     # ERD + 实体字典
│   ├── 02_state_machine_spec.md        # 状态机完整规格 + Mermaid 图
│   └── 03_test_parameter_space.md      # 参数定义 + Pairwise 组合
├── phase4/
│   ├── 01_test_model_specification.md  # 测试模型完整规格书
│   ├── 02_state_transition_graph.md     # 状态转换图 + 路径列表
│   └── 03_coverage_criteria.md         # 覆盖准则 + 最小测试集
├── phase5/
│   ├── 01_testcase_collection.md       # 完整测试用例集 (每条 ~80行)
│   ├── 02_test_suite_summary.md        # 统计摘要 + 执行计划
│   └── 03_traceability_matrix.md       # 双向追溯矩阵 + 缺口分析
└── quality_report.md                   # 全流程质量评估报告
```

---

## 🏛️ 架构

### 整体流程

```
用户输入 → [预处理引擎] → [五阶段流水线] → [输出层]
              ↓                ↓               ↓
         格式规范化    Phase1→2→3→4→5    16+ 文件产物
         歧义检测       ↓               质量报告
         输入验证    [Quality Gate ×5]
                      ↓ (任一门禁不通过则)
                 [错误修复 / 降级处理]
```

### 五阶段详解

| 阶段 | 名称 | 核心产出 | 关键能力 |
|------|------|---------|---------|
| **Phase 1** | 需求预处理 | 结构化需求 + AC + BVA/EP | SMART-V 提取、冲突检测、依赖图谱 |
| **Phase 2** | 代码分析 | 架构图 + DFD + 缺陷雷达 | 静态分析、复杂度度量、安全检查 |
| **Phase 3** | 领域建模 | ERD + 状态机 + 参数空间 | DDD 建模、状态完备性验证、组合优化 |
| **Phase 4** | MBT 设计 | 测试模型 + 覆盖准则 + 路径集 | 贪心算法最小测试集、风险导向优先级 |
| **Phase 5** | 用例生成 | 用例集 + 追溯矩阵 + 统计报告 | 三重去重、自动化适配、CI/CD集成 |

---

## 📖 使用指南

### 适用场景

| 场景 | 推荐命令 | 配置建议 |
|------|---------|---------|
| 新功能首次测试 | `/testcase-generator [功能描述]` | `--depth=full` |
| 迭代回归测试 | `/testcase-generator --format=json [变更描述]` | `--priority=P0,P1` |
| API 契约测试 | `/testcase-generator openapi.yaml` | 自动检测 API Spec 模式 |
| 安全审计 | `/testcase-generator [模块] --depth=exploratory` | 关注 Phase 2 安全检查和 DEF- radar |
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

创建 `test-config.json` 来自定义所有行为：

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

详细配置项参考 `SKILL.md` 中的「默认配置」章节。

---

## 🛡️ 质量保障体系

### 质量门禁

每个阶段完成后自动执行质量检查，包含 **30+ 个检查维度**：

| 阶段 | 主要检查维度 | 通过阈值 |
|------|------------|---------|
| P1 需求预处理 | 完整性、准确性、可测试性、一致性、幻觉防护 | ≥ 80 分 (B 级) |
| P2 代码分析 | 分析范围、数据流、缺陷依据、需求对齐 | ≥ 80 分 (B 级) |
| P3 领域建模 | ERD 质量、状态机完备性、参数空间、跨阶段一致 | ≥ 85 分 (B+ 级) |
| P4 MBT 设计 | 模型正确性、覆盖准则合理性、可操作性、优化 | ≥ 85 分 (B+ 级) |
| P5 用例生成 | 覆盖完整性、用例质量、去重效果、规范性 | ≥ 90 分 (A 级) |

### 度量指标

| 指标 | 目标 | 危险阈值 |
|------|------|---------|
| 需求覆盖率 | 100% | < 95% |
| 边界覆盖率 | 100% | < 90% |
| 幻觉率 | < 5% | > 15% |
| 用例有效率 (去重后) | > 85% | < 70% |
| 追溯闭合率 | 100% | < 95% |

---

## 📁 项目结构

```
testcase-generator/
├── SKILL.md                              # 🔑 Skill 主文件 (核心入口)
├── README.md                             # 📖 本文件
├── run_package.bat                       # 🛠️ Windows 打包脚本
│
├── config/                               # ⚙️ 配置文件
│   ├── example-config.json               #   配置示例
│   └── testcase-config-schema.json       #   JSON Schema 校验定义
│
├── prompts/                              # 📝 各阶段提示词 (AI 执行指令)
│   ├── phase0_input_preprocessing_prompt.md
│   ├── phase1_requirements_prompt.md     #   阶段1: 需求预处理引擎
│   ├── phase2_code_analysis_prompt.md    #   阶段2: 代码分析引擎
│   ├── phase3_domain_analysis_prompt.md  #   阶段3: 领域建模引擎
│   ├── phase4_mbt_design_prompt.md      #   阶段4: MBT 设计引擎
│   └── phase5_testcase_generation_prompt.md # 阶段5: 用例生成引擎
│
├── scripts/                              # 🐍 Python 工具脚本
│   ├── prd_reader.py                    #   PRD 文件读取与解析
│   └── _do_package.py                   #   打包脚本（生成 ZIP）
│
├── templates/                            # 📋 输出模板 (产物格式规范)
│   ├── requirements_template.md          #   需求规格说明书模板 v2.0
│   ├── state_diagram_template.md         #   状态机规格模板 v2.0
│   └── testcase_template.md              #   测试用例模板 v2.0
│
└── resources/                            # 📚 参考资源
    ├── quality_checklist.md              #   质量检查指南 v2.0 (含全部门禁规则)
    └── testcase_formats.md              #   测试用例格式参考 v2.0 (8种格式)
```

---

## 🔄 版本历史

### v2.0.0 (2026-04-04) — 全面重构

#### 新增
- 🏗️ 流水线架构 + 质量门禁系统
- ⚙️ 完整的配置系统 (`test-config.json`)
- 🔄 错误分类与自动恢复策略
- 🔍 歧义/冲突/幻觉三重检测机制
- 📊 量化质量评分与度量基线
- 🗺️ 双向可追溯矩阵 (正向 + 逆向)
- 🧹 三重用例去重 (语法 + 语义 + 覆盖)
- 🤖 自动化代码骨架 (Python/TypeScript 示例)
- 📐 Pairwise 参数空间优化
- 🛡️ OWASP 安全检查集成

#### 改进
- 所有提示词从简单列表升级为完整执行协议
- 模板增加版本控制、变更追踪、元数据标准
- 质量检查从简单 checklist 升级为量化评分体系
- 增加 8 种测试用例输出格式的详细规范

### v1.1.0 — 增强版
- 增加网络调研能力
- 增加模板系统和资源文件

### v1.0.0 — 初始版本
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
  <sub>Built with ❤️ by testcase-generator v2.0 | 基于 AI 的生产级测试用例生成方案</sub>
</p>
