# TestCase Generator Skill v2.1.0

AI 驱动的生产级测试用例生成 Skill，基于 MBT（Model-Based Testing）方法论，采用 6 阶段流水线：

`Phase 0 输入预处理 -> Phase 1 需求预处理 -> Phase 2 代码分析 -> Phase 3 领域建模 -> Phase 4 MBT 设计 -> Phase 5 用例生成`

## 核心能力

- `Phase 0`：输入校验、规范化、质量评分、增强建议
- `Phase 1`：需求摘要、可测需求、边界条件、NFR 与影响分析
- `Phase 2`：代码结构、数据流、缺陷雷达、并发分析、契约测试推导
- `Phase 3`：业务领域模型、状态机、参数空间、事件风暴、时序约束
- `Phase 4`：测试模型规范、状态迁移图、覆盖准则、变异测试策略、错误猜测清单
- `Phase 5`：测试用例集、套件摘要、追踪矩阵、混沌工程场景、测试数据工厂
- `Quality`：阶段门禁、Schema 校验、可追溯性、反馈闭环

## 仓库结构

```text
test-generator/
├── SKILL.md
├── README.md
├── config/
│   ├── example-config.json
│   └── testcase-config-schema.json
├── prompts/
│   ├── phase0_input_preprocessing_prompt.md
│   ├── phase1_requirements_prompt.md
│   ├── phase2_code_analysis_prompt.md
│   ├── phase3_domain_analysis_prompt.md
│   ├── phase4_mbt_design_prompt.md
│   └── phase5_testcase_generation_prompt.md
├── resources/
│   ├── feedback_template.md
│   ├── quality_checklist.md
│   └── testcase_formats.md
├── scripts/
│   ├── _do_package.py
│   ├── capability_audit.py
│   └── prd_reader.py
└── templates/
    ├── requirements_template.md
    ├── state_diagram_template.md
    └── testcase_template.md
```

## 快速使用

```bash
/testcase-generator 为订单系统生成测试用例
/testcase-generator ./requirements/order-system.md
/testcase-generator --format=gherkin --priority=P0,P1 支付模块
/testcase-generator --config=./config/example-config.json 订单管理系统
```

## 配置

- 默认示例：`config/example-config.json`
- Schema：`config/testcase-config-schema.json`
- 关键 v2.1 能力：
  - `input_preprocessing`
  - `chaos_engineering`
  - `mutation_testing`
  - `error_guessing`
  - `quality_thresholds`

## 反馈闭环

v2.1 增加了反馈闭环机制，建议在真实执行后回填：

- 用例执行结果
- 漏测场景
- 质量评分调整
- 业务规则修正

模板见 `resources/feedback_template.md`。

## 一致性审计

新增审计脚本用于检查能力矩阵是否落地：

```bash
python scripts/capability_audit.py
python scripts/capability_audit.py --format json
```

审计会检查：

- `SKILL.md` 版本与 `README.md` 是否一致
- Prompt、模板、资源文件是否齐全
- Schema 是否有效
- 示例配置是否能被 Schema 验证
- 反馈闭环模板是否存在

## 打包

```bash
python scripts/_do_package.py
```

输出文件为根目录下的 `testcase-generator.zip`。
