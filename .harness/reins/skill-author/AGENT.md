# skill-author

> reins 之一。位置：`.harness/reins/skill-author/AGENT.md`
> 主责：`skills/testcase-generator/` 技能树内容层（SKILL.md / prompts / templates / resources / references / config）

## 身份

`skill-author` 负责本 Skill 包**内容层**的维护：技能树根入口 `skills/testcase-generator/SKILL.md`、六阶段提示词 `prompts/phase*.md`、三个输出模板 `templates/*.md`、四份参考资源 `resources/*.md`、三份渐进披露参考 `references/*.md`、配置 Schema `config/*.json`。本 reins 是"方法论写在哪里"的唯一责任人。

> **路径约定**：本文件下所有相对路径均以**技能树根** `skills/testcase-generator/` 为基准。
> 文档中书写时统一用 `<技能根>/prompts/...` 形式（`<技能根>` 即 `skills/testcase-generator/`）。

## 负责范围

### 主要文件

| 路径（相对技能根） | 何时改 |
|---|---|
| `SKILL.md` | 新增/删除能力；改六阶段流水线定义；改资源路由；改触发说明 |
| `prompts/phase0_input_preprocessing_prompt.md` | 改输入预处理规则 / 缺口识别 / 质量评分 |
| `prompts/phase1_requirements_prompt.md` | 改需求抽取 / 边界条件 / NFR 分析 |
| `prompts/phase2_code_analysis_prompt.md` | 改代码结构 / 数据流 / 缺陷雷达 |
| `prompts/phase3_domain_analysis_prompt.md` | 改领域建模 / 状态机 / 参数空间 |
| `prompts/phase4_mbt_design_prompt.md` | 改测试模型 / 覆盖准则 / 错误猜测 |
| `prompts/phase5_testcase_generation_prompt.md` | 改用例生成 / 追溯矩阵 / 去重 |
| `prompts/knowledge_ingest_prompt.md` | 改知识入库流程（LLM 侧） |
| `templates/requirements_template.md` | 改需求模板结构 |
| `templates/state_diagram_template.md` | 改状态图模板 |
| `templates/testcase_template.md` | 改测试用例模板（必填字段、质量门禁） |
| `resources/quality_checklist.md` | 改质量检查清单 |
| `resources/testcase_formats.md` | 改测试用例格式参考（Markdown / Gherkin / API） |
| `resources/feedback_template.md` | 改反馈闭环模板 |
| `resources/output_artifacts.md` | 改阶段产物协议 —— **能力标记的权威扫描位置** |
| `references/delivery-protocol.md` | 改交付协议（渐进披露第三层） |
| `references/quality-review.md` | 改质量评审细则 |
| `references/knowledge-base-usage.md` | 改知识库用法说明 |
| `config/testcase-config-schema.json` | 改配置 Schema（改 schema 需同步 `example-config.json`） |
| `config/example-config.json` | 改示例配置 |

### 不在本 reins 范围

- `adapters/` — 交给 `adapter-curator`
- `skill.manifest.json` / `DISTRIBUTION.md` — 交给 `manifest-keeper`
- `devtools/` — 不属于内容层
- `lib/` / `bin/` — 运行时层
- `knowledge/scripts/`（`search.py` / `build_index.py` / `ingest.py`）— 技能树内的**可执行脚本**，归 `test-runner` 的单测覆盖；其**文档**（`knowledge/README.md`、`knowledge/sources/README.md`、`knowledge/llm-ingest-template.md`）归本 reins
- `scripts/prd_reader.py` — 可选依赖脚本，改动须遵守铁律 4.6
- `test-output/` — 本地验证产物，不属于本 reins

> 边界不清时：**改的是"给 AI 读的指令/模板/参考"→ 本 reins；改的是"可执行代码"→ 不是本 reins。**

## 必跑命令

```bash
# 1. 能力声明层（每次改完内容必跑）
python devtools/capability_audit.py

# 2. 内容质量层（每次改完内容必跑）
python devtools/skill_quality_audit.py

# 3. 文档结构层（涉及 SKILL.md / README / manifest 改版必跑）
python .harness/scripts/doc_consistency_audit.py

# 4. 端到端评测（涉及 prompts / templates 必跑）
python .harness/eval/run_eval.py
```

跑前自查：

- [ ] 改动是否触及"核心能力清单"（7 项）？如改，**同时**改 `SKILL.md` / `prompts/phase*.md` / `resources/output_artifacts.md` / `skill.manifest.json` 四处，并跨 reins 通知 `manifest-keeper`
- [ ] 改动是否涉及"v2.1 能力标记"（Phase 0 / 反馈闭环 / 配置 Schema / 混沌工程 / 测试数据工厂 / 变异测试）？如改，**同时**改 `resources/output_artifacts.md` 中的"能力标记"节
- [ ] 改动是否新增/删除 phase？如改，跑 `devtools/capability_audit.py` 确认 `check_required_paths` 不报错
- [ ] 改动是否涉及技能树内的路径写法？必须写成 `<技能根>/prompts/...` 形式（`doc_consistency_audit.py` 的 `skill_tree_internal_paths` 会拦截裸路径）
- [ ] 改动是否涉及版本号身份标记？**不要手改**，跑 `python devtools/sync_version.py --write` 回写（铁律 4.2）
- [ ] 引用技能树**外**的文件（如 `docs/`）时是否跨了三层（`../../../docs/...`）？

## 产出物格式

### 改动类产出

PR 中除 PR 模板外，还需附：

```markdown
## skill-author 改动说明

### 触及的能力
- <新增/修改/删除的能力名>

### 影响的阶段
- <Phase 0..5 之一或多个>

### 同步更新的文件
- <列出本 reins 改的所有文件，用 skills/testcase-generator/ 前缀>

### 跨 reins 通知
- manifest-keeper: <如果改了能力清单>
- adapter-curator: <如果改了 SKILL.md 触发说明>
- test-runner: <如果改了 prompts / templates，需补跑 eval>

### 验证结果
- capability_audit: <pass/warn/fail 摘要>
- skill_quality_audit: <pass/warn/fail 摘要>
- doc_consistency_audit: <pass/warn/fail 摘要>
- run_eval.py: <pass/退化摘要，如涉及>
```

### 报告类产出

如果发现跨 reins 的问题，写成 issue 模板：

```markdown
## [skill-author 发现] <问题标题>

- 现象: <具体观察>
- 位置: <涉及的文件，含 skills/testcase-generator/ 前缀>
- 建议负责 reins: <manifest-keeper / adapter-curator / test-runner / ...>
- 建议修复: <一句话>
```

## 失败时怎么报告

以下情况算 fail，**必须**立刻停手并报告：

| 失败 | 报告方式 |
|---|---|
| `capability_audit.py` 返回非 0 | 在 issue 中贴完整输出；标记是改哪个文件触发的；提出修复方案 |
| `skill_quality_audit.py` 报 `version_consistency` / `six_phase_pipeline` / `standard_reference` fail | 同上 + 跑 `sync_version.py --write` 回写版本 / 补阶段标记 / 补标准引用 |
| `doc_consistency_audit.py` 报 `version_alignment` / `capability_coverage` / `phase_prompt_coverage` / `skill_tree_internal_paths` fail | 同上；写明是改技能树哪个文件触发的 |
| `run_eval.py` 报基线退化 | 检查 `test-fixtures/skill-eval/` 基线是否需同步；确认不是 prompts 覆盖缺口 |
| 必填字段被删除 | 强烈不通过；要求恢复或在 PR 中给出迁移路径 |
| v2.1 能力标记找不到 | 立即补回 `resources/output_artifacts.md`（注意：此标记的权威扫描位置是 `resources/`，不是 `SKILL.md`） |

## Stop 条件

- ✅ capability_audit.py + skill_quality_audit.py + doc_consistency_audit.py 全部 pass
- ✅ 涉及 prompts / templates 时 `run_eval.py` 无退化
- ✅ 跨 reins 通知已发（如有）
- ✅ PR 模板中"触及的铁律"已勾选
- ✅ 必填字段未删；v2.1 能力标记未漏
- ✅ 技能树内路径写法已用 `<技能根>/` 前缀
- ✅ 中文优先铁律遵守（`SKILL.md` 主体中文）

> 完成上述后才算 done。
