# .harness/eval/baselines/ — 基线来源与已选子集

本目录是 `testcase-generator` Skill 的离线 eval **基线**的元数据
仓库。**不**保存基线产物本身——基线产物已经在仓库根 `test-output/`
里了（这些是过去 v2.0.x / v2.1.0 开发期的真实运行结果）。

## 为什么这里没有 `.md` 产物副本

- `test-output/` 已经被列入 `skill.manifest.json` 的「分发排除」，
  永远不会进入 `.skill` / `.zip`。`.harness/` 也属于开发工具元数据
  （不入包），所以把基线产物**复制**到这里既冗余又违反「铁律 4.1
  入包边界」的设计意图。
- 真实基线文件在 `test-output/` 即可读。eval 流水线
  (`run_eval.py`) 的「expected_outputs」检查就是直接读那里——任何
  想复现基线的人只需要 `git checkout` 到对应版本即可。

## 哪些子集被选为基线

下表列出当前 v2.1.0 选用作 eval 基线的 `test-output/` 子集。每个
子集都对应一个 `test-fixtures/skill-eval/` 下的样本。

| 期望产物（相对 `test-output/`） | 对应 fixture | 用途 |
|---|---|---|
| `phase0/00_input_validation_report.md` | `ambiguous_requirement.md` | 验证 Phase 0 降级路径 |
| `phase0/00_enhancement_suggestions.md` | `ambiguous_requirement.md` | 验证 Phase 0 增强建议 |
| `phase1/01_requirements_summary.md` | `login_prd.md` | 验证标准交付（需求驱动） |
| `phase2/04_concurrency_analysis.md` | `bugfix_regression.py` | 验证代码辅助模式 |
| `phase2/05_contract_test_derivation.md` | `order_openapi.yaml` | 验证 API 契约推导 |
| `phase3/04_event_storming_model.md` | `order_lifecycle.md` | 验证 MBT 状态建模 |
| `phase4/04_mutation_testing_strategy.md` | `order_lifecycle.md` | 验证 MBT 覆盖准则 |
| `phase5/01_testcase_collection.md` | `login_prd.md` / `bugfix_regression.py` / `order_openapi.yaml` | 验证最终用例集生成 |

**未选作基线**的 `test-output/` 文件（仅供人工查阅，不参与 eval 门禁）：

| 文件 | 原因 |
|---|---|
| `phase0/00_normalized_input.md` | 是 `00_input_validation_report.md` 的下游，规范输入产物形态非 v2.1 必选 |
| `phase1/02_testable_requirements.md` / `03_boundary_conditions.md` / `04_nfr_and_impact_analysis.md` | 阶段内部详细产物，目前与 fixture 没有显式 1:1 映射 |
| `phase3/04_event_storming_model.md` 之外 | v2.1 实际未跑该阶段其它产物 |
| `phase5/04_chaos_engineering_scenarios.md` | 来自订单系统的混沌工程示例，与当前 5 个 fixture 不匹配 |
| `skill-eval/ambiguous_requirement.md` / `formal_login_cases.md` / `login.feature` / `order_api_cases.md` | 历史示例输出，无对应 fixture |
| `quality_report.md` / `skill-validation-order-system-report.md` / `test-input-order-system.md` / `示例PRD_用户登录模块.md` | 集成验证报告与历史示例，非基线 |

## 怎么更新基线

如果 `test-output/` 里的某个产物经过 v2.2+ 的改动变得不准确（例
如 prompt 重写导致产物格式变了），按以下流程：

1. 用新版本 Skill 跑出 v2.2+ 的产物，覆盖 `test-output/` 对应文件。
2. 更新 `EXPECTED_OUTPUTS.md` 和 `run_eval.py` 的 `expected_outputs`。
3. 在本 README 表格里更新对应行（必要时加「v2.2 起基线」备注）。
4. 在下一个版本的 `changelogs/v<NEW>.md` 里记录这次基线重置。

> 不要为了"让 eval 通过"而修改 `test-output/`——基线是历史真相，不
> 是测试期望。修改期望请改 `EXPECTED_OUTPUTS.md`。

## 跨平台 / 跨仓库的基线复用

如果将来要把 eval 流水线移植到其他 testcase-generator 派生项目：

1. 复制 `.harness/eval/` 整个目录（包括 `EXPECTED_OUTPUTS.md` 和
   本 `baselines/README.md`）。
2. 在新项目里把 `test-output/` 里的对应产物落到同名相对路径。
3. 调整 `run_eval.py` 里 `FIXTURE_DIR` / `OUTPUT_DIR` 常量（默认
   指向 `test-fixtures/skill-eval/` 和 `test-output/`，可由命令行
   覆盖）。
4. 重跑 `python .harness/eval/run_eval.py --strict` 验证基线对齐。
