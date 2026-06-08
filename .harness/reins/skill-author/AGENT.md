# skill-author

> reins 之一。位置：`.harness/reins/skill-author/AGENT.md`
> 主责：SKILL.md / prompts/ / templates/ / resources/ 维护

## 身份

`skill-author` 负责本 Skill 包**内容层**的维护：根入口 `SKILL.md`、六个阶段提示词 `prompts/phase*.md`、三个输出模板 `templates/*.md`、四份参考资源 `resources/*.md`。本 reins 是"方法论写在哪里"的唯一责任人。

## 负责范围

### 主要文件

| 路径 | 何时改 |
|---|---|
| `SKILL.md` | 新增/删除能力；改六阶段流水线定义；改资源路由；改触发说明 |
| `prompts/phase0_input_preprocessing_prompt.md` | 改输入预处理规则 / 缺口识别 / 质量评分 |
| `prompts/phase1_requirements_prompt.md` | 改需求抽取 / 边界条件 / NFR 分析 |
| `prompts/phase2_code_analysis_prompt.md` | 改代码结构 / 数据流 / 缺陷雷达 |
| `prompts/phase3_domain_analysis_prompt.md` | 改领域建模 / 状态机 / 参数空间 |
| `prompts/phase4_mbt_design_prompt.md` | 改测试模型 / 覆盖准则 / 错误猜测 |
| `prompts/phase5_testcase_generation_prompt.md` | 改用例生成 / 追溯矩阵 / 去重 |
| `templates/requirements_template.md` | 改需求模板结构 |
| `templates/state_diagram_template.md` | 改状态图模板 |
| `templates/testcase_template.md` | 改测试用例模板（必填字段、质量门禁） |
| `resources/quality_checklist.md` | 改质量检查清单 |
| `resources/testcase_formats.md` | 改测试用例格式参考（Markdown / Gherkin / API） |
| `resources/feedback_template.md` | 改反馈闭环模板 |
| `resources/output_artifacts.md` | 改阶段产物协议 |

### 不在本 reins 范围

- `adapters/` — 交给 `adapter-curator`
- `skill.manifest.json` / `DISTRIBUTION.md` — 交给 `manifest-keeper`
- `devtools/` — 不属于内容层
- `lib/` / `bin/` — 运行时层
- `test-output/` — 本地验证产物，不属于本 reins

## 必跑命令

```bash
# 1. 能力声明层（每次改完内容必跑）
python devtools/capability_audit.py

# 2. 内容质量层（每次改完内容必跑）
python devtools/skill_quality_audit.py

# 3. 文档结构层（涉及 SKILL.md 改版必跑）
python .harness/scripts/doc_consistency_audit.py
```

跑前自查：

- [ ] 改动是否触及"核心能力清单"（7 项）？如改，**同时**改 `SKILL.md` / `prompts/*` / `resources/output_artifacts.md` / `skill.manifest.json`，并跨 reins 通知 `manifest-keeper`
- [ ] 改动是否涉及"v2.1 能力标记"（阶段 0 / 反馈闭环 / 配置 Schema / 混沌工程 / 测试数据工厂 / 变异测试）？如改，**同时**改 `resources/output_artifacts.md` 中的"能力标记"节
- [ ] 改动是否新增/删除 phase？如改，跑 `devtools/capability_audit.py` 确认 `check_required_paths` 不报错
- [ ] 改动是否涉及 SKILL.md front matter 的 `version`？如改，**同时**改 `README.md` 标题 / `skill.manifest.json` "版本"字段（铁律 4.2）

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
- <列出本 reins 改的所有文件>

### 跨 reins 通知
- manifest-keeper: <如果改了能力清单>
- adapter-curator: <如果改了 SKILL.md 触发说明>

### 验证结果
- capability_audit: <pass/warn/fail 摘要>
- skill_quality_audit: <pass/warn/fail 摘要>
- doc_consistency_audit: <pass/warn/fail 摘要>
```

### 报告类产出

如果发现跨 reins 的问题，写成 issue 模板：

```markdown
## [skill-author 发现] <问题标题>

- 现象: <具体观察>
- 位置: <涉及的文件>
- 建议负责 reins: <manifest-keeper / adapter-curator / ...>
- 建议修复: <一句话>
```

## 失败时怎么报告

以下情况算 fail，**必须**立刻停手并报告：

| 失败 | 报告方式 |
|---|---|
| `capability_audit.py` 返回非 0 | 在 issue 中贴完整输出；标记是改哪个文件触发的；提出修复方案 |
| `skill_quality_audit.py` 报 `version_consistency` / `six_phase_pipeline` / `standard_reference` fail | 同上 + 在 SKILL.md 头部加版本号 / 阶段标记 / 标准引用 |
| `doc_consistency_audit.py` 报 `version_alignment` / `capability_coverage` / `phase_prompt_coverage` fail | 同上；写明是改 SKILL.md 还是改 manifest 触发的 |
| 必填字段被删除 | 强烈不通过；要求恢复或在 PR 中给出迁移路径 |
| v2.1 能力标记找不到 | 立即补回 `SKILL.md` 或 `resources/output_artifacts.md` |

## Stop 条件

- ✅ capability_audit.py + skill_quality_audit.py + doc_consistency_audit.py 全部 pass
- ✅ 跨 reins 通知已发（如有）
- ✅ PR 模板中"触及的铁律"已勾选
- ✅ 必填字段未删；v2.1 能力标记未漏
- ✅ 中文优先铁律遵守（SKILL.md 主体中文）

> 完成上述后才算 done。
