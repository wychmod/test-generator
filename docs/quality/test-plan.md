# testcase-generator Skill 测试计划

## 1. 行业基准

本测试计划用于验证 `testcase-generator` 生成的测试设计与测试用例是否达到可评审、可执行、可追溯的交付标准。

采用以下基准：

- ISO/IEC/IEEE 29119-3:2021：测试文档结构、测试设计说明、测试用例说明、测试过程说明。
- Azure Test Plans：测试用例必须验证用户需求；测试步骤应包含 Action 和 Expected Result；支持需求链接、配置、标签和数据驱动。
- Cucumber Gherkin：BDD 输出必须包含 Feature、Scenario、Given、When、Then；Then 必须描述可观测结果。
- ISTQB 测试设计技术：等价类、边界值、决策表、状态迁移、错误猜测、风险优先级。

参考：

- https://www.iso.org/standard/79429.html
- https://learn.microsoft.com/en-us/azure/devops/test/create-test-cases?view=azure-devops
- https://cucumber.io/docs/gherkin/reference/

## 2. 评分维度

| 维度 | 权重 | 验收标准 |
|---|---:|---|
| 字段完整性 | 20 | 包含 ID、标题、前置条件、测试数据、步骤、预期结果、优先级、类型、追溯、假设/缺口 |
| 可执行性 | 20 | 步骤可转化为手工或自动化操作；每步有明确操作对象和输入 |
| 预期结果质量 | 20 | 预期结果可观测、可二元判定，避免“正常”“合理”等模糊词 |
| 覆盖完整性 | 20 | 覆盖正向、负向、边界、权限、安全、状态迁移或回归风险 |
| 追溯与防幻觉 | 20 | 每条正式用例能追溯来源；推断内容明确标记为假设 |

评分阈值：

- A：90-100，可正式交付。
- B：80-89，可交付但需处理轻微警告。
- C：70-79，仅可作为草稿，需要补齐缺口。
- D：<70，不合格，必须重构生成规则或补充输入。

## 3. 测试场景

| 输入 | 目标 | 期望输出 |
|---|---|---|
| `test-fixtures/skill-eval/login_prd.md` | 登录 PRD 生成测试用例 | 覆盖正向、负向、边界、安全锁定、追溯 |
| `test-fixtures/skill-eval/order_openapi.yaml` | API 契约测试 | 覆盖状态码、请求/响应 schema、错误矩阵 |
| `test-fixtures/skill-eval/order_lifecycle.md` | 状态迁移与 MBT | 覆盖状态、转换、非法路径、最小路径集 |
| `test-fixtures/skill-eval/ambiguous_requirement.md` | 模糊需求降级处理 | 输出风险摘要、缺失信息、降级草稿，不得声称正式用例 |
| `test-fixtures/skill-eval/bugfix_regression.py` | Bugfix 回归测试设计 | 覆盖复现路径、修复验证、邻近风险 |

## 4. 自动化检查

静态检查：

```bash
python devtools/capability_audit.py
python devtools/skill_quality_audit.py --format markdown
```

生成物检查：

```bash
python devtools/skill_quality_audit.py --outputs test-output/skill-eval --format json
```

审计范围：

- 静态审计覆盖 `SKILL.md`、`prompts/phase0-5`、`resources/*`、`templates/*` 中的版本、阶段、标准引用、必备字段和质量门禁。
- 正式测试用例输出按 100 分制评分；字段完整性、可执行性、预期结果质量、覆盖类型信号、追溯与假设/缺口标记各 20 分。
- 正式测试用例单文件分数必须 `>= 90`，输出目录的正式用例通过率必须 `>= 90%`。
- Gherkin 输出必须包含 Feature、Scenario、Given、When、Then。
- API 输出必须包含 Request、Expected Response、Status、Schema、Error Matrix。

分发回归：

```bash
python devtools/package_skill.py
npm test
npm pack --dry-run
```

## 5. 不合格处理

- 字段缺失：补模板或主入口最小交付协议。
- 版本漂移：统一模板、资源、质量指南到 v2.1。
- 阶段不一致：统一为 Phase 0-5 六阶段流水线。
- 标准引用过时：以 ISO/IEC/IEEE 29119-3:2021 为当前标准，旧 IEEE 829 不作为当前合规依据。
- 模糊输入被伪造成正式用例：强化风险摘要、缺失信息清单和降级草稿规则。
