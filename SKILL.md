---
name: testcase-generator
description: |
  AI 驱动的生产级测试用例生成器 - 基于 MBT（Model-Based Testing）方法论。
  五阶段流水线：需求预处理 → 代码分析 → 领域建模 → MBT设计 → 用例生成。
  支持多种输入源（需求文档/代码/API规范/自然语言），输出可追溯、可执行的高质量测试用例。
version: 2.1.0
author: Test Generator Team
license: MIT
tags:
  - testing
  - testcase-generation
  - MBT
  - model-based-testing
  - quality-assurance
  - automation

metadata:
  last_updated: 2026-04-06
  compatibility:
    min_agent_version: "1.0.0"
  supported_inputs:
    - requirements-doc
    - user-story
    - source-code
    - api-specification
    - natural-language
  output_formats:
    - markdown
    - gherkin
    - json
  estimated_time:
    small: "5-10 min"
    medium: "15-30 min"
    large: "45-90 min"
---

# 🔬 TestCase Generator v2.1 — 生产级测试用例生成器

> **核心理念**：每一个生成的用例都必须可追溯、可执行、可验证。
> **v2.1 升级亮点**：新增 Phase 0 输入预处理引擎、非功能需求完整提取、并发/契约测试分析、事件风暴建模、变异测试策略、混沌工程场景、测试数据工厂。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        输入层 (Input Layer)                          │
│  需求文档 │ 用户故事 │ 源代码 │ API Spec │ 自然语言描述              │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Phase 0: 输入预处理引擎 (NEW in v2.1)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 输入验证器    │→│ 格式规范化   │→│ 歧义检测器    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 结构化提取   │→│ 质量评估     │→│ 增强建议      │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   六阶段处理流水线 (Pipeline)                         │
│                                                                     │
│  Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5  │
│  输入预处理   需求预处理   代码分析    领域建模    MBT设计     用例生成  │
│    ↓           ↓          ↓          ↓           ↓         ↓       │
│  质量门禁    质量门禁    质量门禁    质量门禁    质量门禁   质量门禁    │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      反馈闭环 (Feedback Loop - NEW)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 用户反馈收集  │→│ 质量度量分析  │→│ 模型持续改进  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      输出层 (Output Layer)                           │
│  test-output/                                                         │
│  ├── phase0/   (输入预处理制品) ← NEW                                │
│  ├── phase1/   (需求制品)    ├── phase4/   (MBT模型)                │
│  ├── phase2/   (代码分析)    ├── phase5/   (测试用例集)              │
│  ├── phase3/   (领域模型)    └── quality_report.md (质量报告)        │
└─────────────────────────────────────────────────────────────────────┘
```

## 快速使用

```bash
# 基本用法
/testcase 为用户登录模块生成测试用例

# 基于文件（支持 PDF 和 Markdown）
/testcase ./requirements/user-auth.md
/testcase ./requirements/prd.pdf

# 指定选项
/testcase --format=gherkin --priority=P0,P1 --depth=full 支付模块API测试

# 完整配置模式
/testcase --config=./test-config.json 订单管理系统
```

### 文件输入协议 (File Input Protocol)

**支持的文件格式：**

| 格式 | 扩展名 | 说明 | 依赖 |
|------|--------|------|------|
| Markdown | `.md`, `.markdown` | 直接读取文本内容 | 无 |
| PDF | `.pdf` | 通过 pdfplumber 提取文本 | `pip install pdfplumber` |

**文件路径处理规则：**

```yaml
file_input_handling:
  path_resolution:
    - 支持绝对路径: `D:\docs\prd.pdf`
    - 支持相对路径: `./requirements/prd.md`
    - 支持空格和中文路径: `./需求文档/产品需求.pdf`

  extraction_priority:
    1. 如果是 .pdf 文件 → 调用 prd_reader.py 的 PDF 提取逻辑
    2. 如果是 .md 文件 → 直接读取内容
    3. 其他文件 → 尝试作为文本读取

  content_preprocessing:
    - 移除 PDF 页眉页脚（如果可识别）
    - 规范化换行符
    - 识别并保留文档结构（标题/列表/表格/代码块）
    - 记录原始文件元信息（文件名/页数/大小）

  error_handling:
    file_not_found:
      action: "提示用户检查文件路径"
      example: "错误: 文件不存在 ./prd.pdf，请确认路径是否正确"
    pdf_parse_error:
      action: "提示安装依赖或使用 OCR"
      example: "pdfplumber 未安装，请运行: pip install pdfplumber"
    encoding_error:
      action: "尝试 GBK/GB2312 编码回退"
      example: "自动尝试使用 GBK 编码读取"
```

**工作流程：**

```
用户输入: /testcase ./requirements/prd.pdf
                    ↓
         prd_reader.py 识别文件类型 (.pdf)
                    ↓
         调用 pdfplumber 提取文本内容
                    ↓
         提取结果传入 Phase 1 需求预处理
                    ↓
         后续流程不变
```

### 命令参数

| 参数 | 缩写 | 说明 | 默认值 | 可选值 |
|------|-----|------|--------|-------|
| `--format` | `-f` | 输出格式 | `markdown` | `markdown`, `gherkin`, `json` |
| `--priority` | `-p` | 用例优先级过滤 | `all` | `P0`,`P1`,`P2`,`P3` |
| `--depth` | `-d` | 测试深度 | `standard` | `smoke`,`standard`,`full`,`exploratory` |
| `--output` | `-o` | 输出目录 | `./test-output/` | 自定义路径 |
| `--config` | `-c` | 配置文件路径 | 无 | JSON 文件 |
| `--lang` | `-l` | 输出语言 | `auto` | `zh`,`en`,`ja` |
| `--traceability` | `-t` | 可追溯性级别 | `full` | `minimal`,`standard`,`full` |
| `--file` | 无 | PRD文件路径 | 无 | PDF/MD 文件路径 |

---

## 六阶段产物清单

| 阶段 | 名称 | 关键产出 | 文件数 | 依赖阶段 |
|------|------|---------|--------|---------|
| **Phase 0** | 输入预处理 | 规范化输入 + 质量评估 + 增强建议 | 3 | 无 (v2.1 NEW) |
| **Phase 1** | 需求预处理 | 结构化需求 + NFR规格 + 影响映射 + 用户旅程 | 4+ | P0 |
| **Phase 2** | 代码分析 | 代码结构 + 并发分析 + 契约测试 + 缺陷图谱 | 5+ | P1 |
| **Phase 3** | 领域建模 | 业务实体 + 状态机 + 事件风暴 + 时序约束 | 5+ | P1, P2 |
| **Phase 4** | MBT设计 | 测试模型规格 + 变异策略 + 错误猜测清单 + 覆盖准则 | 6+ | P1-P3 |
| **Phase 5** | 用例生成 | 测试用例集 + 混沌工程场景 + 数据工厂 + 追溯矩阵 | 7+ | P1-P4 |

### 详细产物映射

```
phase0/                                    ← NEW in v2.1
  ├── 00_input_validation_report.md       # 输入验证与质量评估报告
  ├── 00_normalized_input.md              # 规范化后的输入内容
  └── 00_enhancement_suggestions.md       # 输入增强建议

phase1/
  ├── 01_requirements_summary.md          # 需求摘要与功能分解
  ├── 02_testable_requirements.md         # 可测试需求条目化清单
  ├── 03_boundary_conditions.md           # 边界条件与等价类划分
  └── 04_nfr_and_impact_analysis.md       # [v2.1] NFR规格 + 影响映射 + 用户旅程

phase2/
  ├── 01_code_structure.md                # 代码结构与调用关系图
  ├── 02_data_flow_analysis.md            # 数据流分析与控制流图
  ├── 03_defect_radar.md                  # 潜在缺陷雷达图
  ├── 04_concurrency_analysis.md          # [v2.1] 并发分析 + 竞态条件检测
  └── 05_contract_test_derivation.md      # [v2.1] API契约测试推导

phase3/
  ├── 01_business_domain_model.md         # 业务领域模型 (ERD)
  ├── 02_state_machine_spec.md            # 状态机规格说明书
  ├── 03_test_parameter_space.md          # 测试参数空间定义
  ├── 04_event_storming_model.md          # [v2.1] 事件风暴领域模型
  └── 05_temporal_constraints.md          # [v2.1] 时序约束 + 集成点地图

phase4/
  ├── 01_test_model_specification.md      # 测试模型完整规格书
  ├── 02_state_transition_graph.md        # 状态转换图 (Mermaid)
  ├── 03_coverage_criteria.md             # 覆盖准则与路径策略
  ├── 04_mutation_testing_strategy.md     # [v2.1] 变异测试策略与算子
  └── 05_error_guessing_checklist.md      # [v2.1] 错误猜测法检查清单

phase5/
  ├── 01_testcase_collection.md           # 完整测试用例集合
  ├── 02_test_suite_summary.md            # 测试套件摘要统计报告
  ├── 03_traceability_matrix.md           # 双向可追溯性矩阵
  ├── 04_chaos_engineering_scenarios.md   # [v2.1] 混沌工程场景集
  └── 05_test_data_factory.md             # [v2.1] 测试数据工厂定义

quality_report.md                          # 全流程质量评估报告
```

---

## 核心能力矩阵

### ✅ 已实现的生产级特性

| 特性类别 | 具体能力 | 成熟度 |
|---------|---------|-------|
| **输入处理** | 多格式输入解析 | ★★★★☆ |
| | 输入验证与错误恢复 | ★★★★☆ |
| | 需求歧义自动检测 | ★★★☆☆ |
| | **[v2.1] 结构化质量评估** | ★★★★☆ |
| **分析引擎** | 依赖关系自动识别 | ★★★★☆ |
| | 圈复杂度计算 | ★★★☆☆ |
| | 缺陷模式匹配 | ★★★☆☆ |
| | **[v2.1] 并发/竞态分析** | ★★★★☆ |
| | **[v2.1] API 契约测试推导** | ★★★★☆ |
| | **[v2.1] 技术债务识别** | ★★★☆☆ |
| **建模能力** | ERD 自动生成 | ★★★★☆ |
| | 状态机推导 | ★★★★☆ |
| | 参数空间压缩 | ★★★☆☆ |
| | **[v2.1] 事件风暴建模** | ★★★★☆ |
| | **[v2.1] 时序约束分析** | ★★★★☆ |
| **用例生成** | 正向/逆向路径覆盖 | ★★★★☆ |
| | 边界值智能选取 | ★★★★☆ |
| | 冗余用例去重 | ★★★★☆ |
| | **[v2.1] 变异测试策略** | ★★★★☆ |
| | **[v2.1] 错误猜测法集成** | ★★★★☆ |
| | **[v2.1] 混沌工程场景生成** | ★★★★☆ |
| | **[v2.1] 测试数据工厂** | ★★★★☆ |
| **质量保障** | 阶段间质量门禁 | ★★★★☆ |
| | 幻觉内容检测 | ★★★☆☆ |
| | 可追溯性保证 | ★★★★★ |
| | **[v2.1] 配置 Schema 校验** | ★★★★☆ |
| | **[v2.1] 反馈闭环机制** | ★★★☆☆ |
| **输出适配** | 多格式输出 | ★★★★☆ |
| | 自动化框架对接 | ★★★☆☆ |
| | 版本变更追踪 | ★★★★☆ |

### 🔄 与 v1.x 的关键差异

| 维度 | v1.x (旧版) | v2.0 (当前) |
|------|------------|------------|
| **架构** | 单体提示词 | 六阶段流水线+门禁 (v2.1: +Phase0) |
| **质量保证** | 自检清单 | 质量门禁+量化指标 |
| **错误处理** | 无 | 完整的错误分类和恢复策略 |
| **可追溯性** | 单向映射 | 双向可追溯矩阵 |
| **输出格式** | 仅 Markdown | Markdown/Gherkin/JSON |
| **配置能力** | 无 | 完整的配置系统 + Schema 校验 (v2.1) |
| **性能优化** | 无 | 参数空间压缩+用例去重 |
| **文档完整性** | 基础 | 生产级完整文档 |
| **NFR 支持** | 无 | 完整 NFR 提取与可测试化 (v2.1) |
| **并发分析** | 无 | 竞态条件+死锁检测 (v2.1) |
| **弹性测试** | 无 | 混沌工程场景生成 (v2.1) |
| **测试数据** | 无 | 数据工厂模式 (v2.1) |

---

## 执行协议 (Execution Protocol)

### 启动检查清单

在开始任何工作之前，Agent **必须**完成以下检查：

```
□ 1. 解析并验证用户输入
   - 输入类型是否支持？（文档/代码/文本）
   - 输入内容是否有效且非空？
   - 是否需要读取外部文件？

□ 2. 确定运行配置
   - 是否有 --config 指定？ → 加载配置文件
   - 否则使用默认配置（见下方「默认配置」章节）

□ 3. 初始化输出目录结构
   - 创建 test-output/{phase1-5}/ 目录
   - 初始化质量报告骨架

□ 4. 设置执行上下文
   - 记录开始时间戳
   - 初始化阶段状态跟踪
   - 准备错误日志记录器
```

### 阶段执行规则

每个阶段的执行遵循严格的 **Gate Protocol**：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Execute   │ ──→ │    Gate     │ ──→ │   Next      │
│  (执行阶段)  │     │  (质量门禁)  │     │  (下一阶段)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Gate Fail? │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                ↓                     ↓
        ┌──────────────┐     ┌──────────────┐
        │ Auto-Repair  │     │ User-Confirm │
        │ (自动修复)    │     │ (用户确认)    │
        └──────────────┘     └──────────────┘
                │                     │
                └─────────┬───────────┘
                          ↓
                   回到 Execute
```

#### 门禁通过标准 (Gate Pass Criteria)

| 度量维度 | 通过阈值 | 警告阈值 | 不通过阈值 |
|---------|---------|---------|-----------|
| 需求覆盖率 | ≥ 95% | 90%-94% | < 90% |
| 产物完整性 | 100% | ≥ 90% | < 90% |
| 内部一致性 | 无冲突 | ≤ 2个警告 | > 2个警告或任何错误 |
| 可追溯性 | 100%映射 | ≥ 95% | < 95% |

### 错误处理策略

```yaml
error_handling:
  classification:
    FATAL:
      description: 无法继续执行的致命错误
      action: 终止执行，输出详细错误报告
      examples:
        - 输入为空或无法解析
        - 输出目录无法创建
    RECOVERABLE:
      description: 可以修复或跳过的错误
      action: 记录警告，尝试自动修复，必要时降级处理
      examples:
        - 部分需求描述不清晰
        - 某些边界条件无法确定
        - 外部资源加载失败
    WARNING:
      description: 不影响主流程的非关键问题
      action: 记录到质量报告，继续执行
      examples:
        - 推荐的最佳实践未被完全遵循
        - 生成的用例数量超出预期范围

  recovery_actions:
    missing_requirement_detail:
      strategy: "标记为 [需人工确认]，基于上下文推断合理默认值"
    code_analysis_failure:
      strategy: "降级为纯需求驱动的测试设计模式"
    state_explosion:
      strategy: "触发状态合并算法，应用抽象层级提升"
    redundant_testcase_detected:
      strategy: "执行语义相似度比较，合并相似度 > 85% 的用例"
```

---

## 默认配置 (Default Configuration)

当用户未提供 `--config` 时，使用以下默认配置：

```json
{
  "$schema": "testcase-config-schema-v2.json",
  "project": {
    "name": "",
    "auto_detect": true,
    "default_language": "zh-CN"
  },
  "pipeline": {
    "phases": ["requirements", "code_analysis", "domain_modeling", "mbt_design", "testcase_generation"],
    "gate_strategy": "strict",
    "continue_on_warning": true,
    "stop_on_error": false
  },
  "generation": {
    "output_format": "markdown",
    "testcase_naming": "TC-{phase}-{module}-{sequence:03d}",
    "priority_distribution": {
      "P0": { "ratio": 0.15, "description": "核心功能/阻塞缺陷" },
      "P1": { "ratio": 0.25, "description": "重要功能/严重缺陷" },
      "P2": { "ratio": 0.35, "description": "一般功能/一般缺陷" },
      "P3": { "ratio": 0.25, "description": "低优先级/建议优化" }
    },
    "boundary_analysis": {
      "method": "robust",  // robust | standard | extreme
      "include_null": true,
      "include_empty": true,
      "include_special_chars": true
    },
    "deduplication": {
      "enabled": true,
      "similarity_threshold": 0.85,
      "method": "semantic"
    }
  },
  "coverage": {
    "requirements_coverage_target": 100,
    "path_coverage_target": "critical+normal",
    "state_coverage_target": 100,
    "boundary_coverage_target": 100
  },
  "quality": {
    "enable_gate_check": true,
    "strict_mode": false,
    "max_warnings_per_phase": 5,
    "hallucination_detection": true
  },
  "output": {
    "directory": "./test-output/",
    "include_metadata": true,
    "include_traceability": true,
    "include_change_log": true,
    "compression": false
  },
  "advanced": {
    "research_enabled": true,
    "research_queries_per_phase": 3,
    "model_optimization": {
      "state_merging_threshold": 0.9,
      "max_states_before_merge": 20,
      "abstraction_level": "balanced"
    }
  }
}
```

---

## 阶段详细说明

> ⚠️ **重要**：每个阶段的详细执行指令请参考 `prompts/` 目录下的对应提示词文件。
> 以下是各阶段的高级概要和质量门禁要求。

### Phase 1: 需求预处理 (Requirements Preprocessing)

**目标**：将原始输入转化为结构化、可测试的需求规格。

**输入**：原始需求 / 用户故事 / 功能描述
**输出**：
- `01_requirements_summary.md` — 结构化需求摘要
- `02_testable_requirements.md` — 可测试需求条目（每条含验收标准）
- `03_boundary_conditions.md` — 边界条件 + 等价类划分

**质量门禁**：
- [ ] 所有功能点均已提取并条目化
- [ ] 每条需求至少包含一条明确的验收标准
- [ ] 边界条件覆盖所有数值/字符串/枚举类型参数
- [ ] 等价类划分无重叠、无遗漏
- [ ] 需求之间的依赖关系已明确标注

**常见失败场景及恢复**：
| 场景 | 检测方式 | 恢复策略 |
|------|---------|---------|
| 需求描述模糊 | AC 中出现「适当」「合理」等词 | 标记 `[需确认]` 并给出推断值 |
| 验收标准缺失 | 某需求无 AC 条目 | 基于行业标准补充默认 AC |
| 边界值不确定 | 参数无取值范围 | 使用领域常识设定安全边界 |

### Phase 2: 代码分析 (Code Analysis)

**目标**：理解实现逻辑，识别测试路径和潜在风险点。

**输入**：源代码 / API 规范 / Phase 1 产物
**输出**：
- `01_code_structure.md` — 代码架构与调用关系
- `02_data_flow_analysis.md` — DFD + 控制流分析
- `03_defect_radar.md` — 潜在缺陷定位与风险评估

**质量门禁**：
- [ ] 所有公开接口/方法已识别
- [ ] 关键数据流端到端可追踪
- [ ] 异常处理路径已枚举
- [ ] 缺陷推测有代码依据（非凭空猜测）

**特殊说明**：
- 若用户提供的是**源代码**：进行实际的静态分析
- 若用户提供的是**需求文档**：构建预期实现的逻辑模型（标记为 `[预期]`）
- 若两者都提供了：以代码为准，需求作为验证基准

### Phase 3: 领域建模 (Domain Modeling)

**目标**：建立业务领域的形式化模型，作为 MBT 的基础。

**输入**：Phase 1 + Phase 2 产物
**输出**：
- `01_business_domain_model.md` — ERD + 业务实体字典
- `02_state_machine_spec.md` — 状态机完整规格
- `03_test_parameter_space.md` — 参数空间定义与约束

**质量门禁**：
- [ ] 业务实体覆盖所有名词概念
- [ ] 实体关系基数正确（1:1, 1:N, M:N）
- [ ] 状态机满足完备性（每个状态的所有可能转换都已定义）
- [ ] 参数空间包含所有输入变量的约束定义
- [ ] 与前两阶段产物一致（术语统一、无矛盾）

**状态爆炸控制**：
当状态数超过阈值时，自动启用以下优化策略：
1. **等价状态合并**：语义相近的状态合并为一个抽象状态
2. **层级分解**：将大状态机拆分为多个子状态机
3. **关注点分离**：按功能域独立建模，最后整合

### Phase 4: MBT 设计 (Model-Based Testing Design)

**目标**：将业务模型转化为可直接驱动用例生成的测试模型。

**输入**：Phase 1-3 全部产物
**输出**：
- `01_test_model_specification.md` — 测试模型完整规格书
- `02_state_transition_graph.md` — 可视化状态转换图
- `03_coverage_criteria.md` — 覆盖准则与最小测试集

**质量门禁**：
- [ ] 测试模型的每个元素都可追溯到业务实体
- [ ] 状态转换图是状态机的真子集（无额外/缺失转换）
- [ ] 覆盖准则符合 ISTQB MBT 标准
- [ ] 最小测试集满足覆盖目标且数量合理
- [ ] 路径优先级分配遵循风险导向原则

**覆盖准则选择指南**：

| 项目类型 | 推荐覆盖级别 | 理由 |
|---------|-------------|------|
| 安全关键系统 | 全路径覆盖 | 失败代价极高 |
| 金融交易系统 | 关键路径 + 边界覆盖 | 平衡成本与风险 |
| 一般业务系统 | 状态对覆盖 + 边界覆盖 | 性价比最优 |
| 原型/MVP | 状态覆盖 | 快速验证核心 |

### Phase 5: 用例生成 (Test Case Generation)

**目标**：基于测试模型，生成完整、可执行、高质量的测试用例集。

**输入**：Phase 1-4 全部产物
**输出**：
- `01_testcase_collection.md` — 完整测试用例集合
- `02_test_suite_summary.md` — 统计摘要与分析报告
- `03_traceability_matrix.md` — 需求↔用例双向追溯矩阵

**质量门禁**：
- [ ] 100% 的可测试需求至少被一个用例覆盖
- [ ] 所有边界条件都有对应的测试用例
- [ ] 每个用例的前置条件充分、步骤可执行
- [ ] 预期结果明确且可自动化验证
- [ ] 无冗余用例（相似度 < 阈值）
- [ ] 优先级分布符合项目风险画像
- [ ] 追溯矩阵完整（正向 + 逆向均可查询）

**用例去重机制**：
1. **语法去重**：标题 + 输入组合完全相同的用例
2. **语义去重**：语义相似度 > 85% 的用例合并
3. **覆盖去重**：覆盖完全相同路径/状态的用例保留最高优先级版本

---

## 输出规范

### 文件命名约定

```
{phase_number}_{sequential_name}.md

示例：
  phase1/01_requirements_summary.md
  phase5/03_traceability_matrix.md
```

### 元数据头规范

每个输出文件的头部必须包含以下元数据：

```markdown
---
generated_by: testcase-generator v2.0.0
timestamp: 2026-04-04T14:00:00+08:00
source_input: [用户提供的输入摘要]
phase: [阶段编号]
version: 1.0
status: draft | reviewed | approved
quality_score: [0-100]
dependencies: [依赖的阶段产物列表]
---
```

### 质量报告规范

最终的质量报告必须包含以下章节：

1. **执行摘要**：整体质量评分 + 通过/不通过结论
2. **各阶段评分卡**：每个维度的得分明细
3. **问题日志**：发现的所有问题及处理结果
4. **覆盖率总览**：需求/路径/状态/边界的覆盖率
5. **改进建议**：针对后续迭代的具体建议
6. **签名确认**：AI 生成标识 + 人工审核区域

---

## 最佳实践指南

### 对于使用者

1. **输入越具体，输出越精准**
   - ❌ 「做一个登录功能的测试」
   - ✅ 「为电商系统的 OAuth2.0 登录功能生成测试用例，参考附件的需求文档」

2. **善用配置文件**
   - 复杂项目建议编写 `test-config.json` 明确指定参数
   - 特别是优先级分布和覆盖目标的定制

3. **分阶段审查**
   - 不要等到最后才看结果
   - 每个 Phase 的产物都可以单独查看和审核

### 对于 Agent 执行者

1. **永远不要凭空创造**
   - 所有实体、状态、转换必须有来源（需求/代码/推理）
   - 标注 `[推断]` 或 `[假设]` 的内容必须在备注中说明依据

2. **质量优先于数量**
   - 10 个高质量用例 > 50 个含糊用例
   - 宁可标注 `[需补充]` 也不编造细节

3. **保持上下文连贯**
   - 后续阶段的产物应引用前面阶段的 ID
   - 术语一旦确定，全程保持一致

---

## 故障排查 (Troubleshooting)

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 输出目录未创建 | 权限不足 | 检查写入权限或指定其他 `-o` 路径 |
| 阶段产物为空 | 输入不足或解析失败 | 查看阶段错误日志，补充更详细的输入 |
| 用例数量异常多/少 | 参数空间爆炸或过度压缩 | 调整 `advanced.model_optimization` 配置 |
| 质量报告显示不通过 | 门禁标准过严 | 降低 `strict_mode` 或调整阈值 |
| 追溯矩阵有空缺 | 需求-用例映射断裂 | 检查 Phase 1 的需求条目化和 Phase 5 的覆盖声明 |

---

## 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| **2.1.0** | **2026-04-06** | **v2.1 大版本升级**: 新增 Phase 0 输入预处理引擎; NFR 完整提取与可测试化; 并发/竞态条件分析; API 契约测试推导; 事件风暴领域建模; 时序约束分析; 变异测试策略; 错误猜测法集成; 混沌工程场景; 测试数据工厂; 配置 Schema 校验; 反馈闭环机制; CHANGELOG/CONTRIBUTING 文档; 从 5 阶段扩展为 6 阶段流水线 | Test Generator Team |
| 2.0.0 | 2026-04-04 | 全面重构：流水线架构、质量门禁系统、配置系统、错误恢复 | Test Generator Team |
| 1.1.0 | 2025-xx-xx | 增加网络调研、模板系统 | Test Generator Team |
| 1.0.0 | 2025-xx-xx | 初始版本：五阶段基础流程 | Test Generator Team |

---

## Phase 0: 输入预处理引擎 (Input Preprocessing Engine) 🆕

> **v2.1 新增阶段** — 在进入需求分析之前，先确保输入质量。

**目标**：对任意格式的原始输入进行验证、规范化、质量评估和增强建议输出。

**输入**：用户提供的任意输入（文档/代码/文本/文件）
**输出**：
- `00_input_validation_report.md` — 输入质量评估报告
- `00_normalized_input.md` — 规范化后的输入内容
- `00_enhancement_suggestions.md` — 输入增强建议

**质量门禁**：
- [ ] 输入格式已被识别并成功解析
- [ ] 输入质量评分 ≥ 60 分（否则给出增强建议）
- [ ] 歧义点已全部标记（不要求消除，但必须识别）
- [ ] 缺失的关键信息已列出

**详细执行指令** → 见 `prompts/phase0_input_preprocessing_prompt.md`

---

## 反馈闭环机制 (Feedback Loop) 🆕

> **v2.1 新增** — 持续改进的核心引擎。

```
┌─────────────────────────────────────────────┐
│              反馈闭环流程                     │
│                                             │
│  1. 用户反馈收集                              │
│     ├── 用例执行结果 (Pass/Fail/Error)       │
│     ├── 缺漏用例报告                         │
│     ├── 质量评分调整                         │
│     └── 业务规则修正                         │
│                                             │
│  2. 质量度量分析                              │
│     ├── 缺陷检出率统计                       │
│     ├── 覆盖率缺口分析                       │
│     ├── 幻觉误报追踪                         │
│     └── 效果 ROI 评估                        │
│                                             │
│  3. 模型持续改进                              │
│     ├── 提示词微调建议                       │
│     ├── 质量阈值自适应                       │
│     ├── 领域知识库更新                       │
│     └── 最佳实践沉淀                         │
└─────────────────────────────────────────────┘
```

### 反馈收集模板

用户可通过以下方式提供反馈：
```markdown
## 测试反馈

### 执行环境
- 执行日期: YYYY-MM-DD
- 执行人: [姓名]
- 测试环境: [开发/测试/预发/生产]

### 用例执行结果
| 用例ID | 结果 | 实际结果与预期差异 | 根因分析 |
|--------|------|------------------|---------|
| TC-P1-xxx | PASS | — | — |
| TC-P1-yyy | FAIL | [描述差异] | [根因] |

### 缺漏报告
| 缺漏场景 | 描述 | 建议 |
|---------|------|------|
| 场景1 | [描述] | [如何补充] |

### 改进建议
[自由文本]
```

---

*此 Skill 遵循 ISTQB MBT（Model-Based Testing）最佳实践，结合 AI 能力进行了增强扩展。*

---

## 附录：prd_reader.py 使用说明

`prd_reader.py` 是本 Skill 的文件预处理器，用于从 PDF 和 Markdown 文件中提取内容。

### 安装依赖

```bash
# PDF 支持（必需）
pip install pdfplumber

# Markdown 无需额外依赖
```

### 命令行使用

```bash
# 基本用法
python prd_reader.py ./requirements/prd.pdf
python prd_reader.py ./requirements/prd.md

# 输出到文件
python prd_reader.py ./prd.pdf --output extracted.txt

# 指定编码
python prd_reader.py ./prd.md --encoding gbk

# 静默模式（适用于管道）
python prd_reader.py ./prd.pdf -q
```

### Python API 使用

```python
from prd_reader import identify_and_extract

result = identify_and_extract("./requirements/prd.pdf")

if result["success"]:
    print(f"内容长度: {len(result['content'])} 字符")
    print(f"文件类型: {result['file_type']}")
    print(result["content"][:500])  # 预览前 500 字
else:
    print(f"错误: {result['error']}")
```
