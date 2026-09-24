# Health Report — testcase-generator 适配器扩展 + .harness 体系建设 (plan_08f98b92)

> 报告时间：2026-06-08
> 范围：本 plan 4 个任务全部完成 + 我后续手动修复了 3 个项目真实问题 + 4 个一致性 warn

## 顶层审计结果（最终）

| 审计脚本 | 结果 | 备注 |
|---|---|---|
| `python .harness/scripts/doc_consistency_audit.py` | **11 PASS / 0 WARN / 0 FAIL** | 含版本号 / 能力矩阵 / 宿主表三方 / npm 入口 / 排他规则 / package_skill 禁入项 |
| `python devtools/capability_audit.py` | **21 PASS / 0 WARN / 0 FAIL** | 含 v2.1 能力标记 / 8 宿主 entry 文件全在 / 6 个 phase prompt 全在 |
| `python devtools/skill_quality_audit.py` | **6 PASS / 0 WARN / 0 FAIL** | 字段 / 标准 / 流水线 / 质量门禁 |
| `node --test test/` | **4 PASS / 0 FAIL** | activation.test.js 全过 |
| `node bin/test-generator.js environments` | 输出 8 宿主 | claude / codebuddy / codex / cursor / openclaw / qoder / trae / windsurf |
| `node bin/test-generator.js activate <env> --dry-run` × 8 | **8 PASS** | 每个宿主 targetDir 计算正确 |

## 计划交付物清单

### 1. 适配器扩展（cycle 1 任务 1）
- 新增 `adapters/codebuddy/SKILL.md`（完整薄适配）
- 新增 `adapters/cursor/cursorrules.md`（软适配，rules 风格）
- 新增 `adapters/windsurf/windsurfrules.md`（软适配，rules 风格）
- 新增 `adapters/trae/SKILL.md`（补齐之前漏建）
- 同步：`skill.manifest.json`（宿主适配入口 dict 8 项 + 运行时文件 + 排除规则）、`HOST_COMPATIBILITY.md`、`lib/activation.js`（8 ENVIRONMENTS）、`devtools/package_skill.py`、`DISTRIBUTION.md`、`.gitignore`、`README.md`、`SKILL.md`（front matter + description）

### 2. .harness 核心（cycle 1 任务 2）
- `.harness/AGENTS.md`：项目宪法（8 节、7 条铁律、reins 索引、PR 模板、失败模式表）
- `.harness/README.md`：体系总览
- `.harness/reins/` × 6：skill-author / adapter-curator / manifest-keeper / packager / auditor / test-runner
- `.harness/reins/README.md`：角色索引
- `.harness/scripts/doc_consistency_audit.py`：6 类一致性护栏（11 检查项）
- `.harness/scripts/README.md`：护栏脚本说明

### 3. .harness 自动化（cycle 1 任务 3）
- `.harness/hooks/precommit.py`：跨平台提交前检查（5 类触发 + --dry-run）
- `.harness/hooks/prepackage.py`：跨平台打包前完整审计
- `.harness/hooks/install-hooks.ps1` + `install-hooks.sh`：钩子安装器
- `.harness/hooks/README.md`：hooks 说明
- `.harness/changelogs/README.md`：命名规范 + 必含字段
- `.harness/changelogs/v2.1.0.md`：当前版本回填
- `.harness/changelogs/v2.3.0-TEMPLATE.md`：发版模板（下一版基线）
- `.harness/eval/run_eval.py`：端到端 eval 流水线（fixture → prompt → 期望产物三维校验，离线可跑）
- `.harness/eval/README.md` + `EXPECTED_OUTPUTS.md` + `baselines/README.md`

### 4. 最终集成验证（cycle 2 任务 4）+ 我手动修复的 7 处一致性问题
| # | 问题 | 修法 |
|---|---|---|
| 1 | SKILL.md front matter 缺 `version:` 字段 | 补 `version: 2.1.0` |
| 2 | SKILL.md 字面未提 7 项核心能力 | 新增"## 核心能力"段，7 项全列 |
| 3 | trae adapter 三方不一致 | 建 `adapters/trae/SKILL.md` + manifest 宿主适配入口 dict 加 trae |
| 4 | `capability_in_output_artifacts` warn | output_artifacts.md 加"覆盖的核心能力"段，7 项映射到 phase |
| 5 | `capability_in_prompts` warn | 6 个 phase prompt 顶部加"对应核心能力"行 |
| 6 | `manifest_excludes_vs_distribution` warn | DISTRIBUTION.md 建议排除表加 devtools/ |
| 7 | `distribution_excludes_vs_manifest` warn | manifest 分发排除加 `bin/test-generator.js` + `lib/activation.js` + 3 个 devtools/*.py 精确路径 |

## 已知遗留（无需修，design 决定）

- `.harness/` 在 manifest 中**未列出**分发排除——它是新加的，AGENTS.md 4.1 段已说明"事实不入包 + 本目录是新增豁免项"。下一版发版前应在 manifest 加 `.harness/**` 到分发排除。
- `lib/activation.js` 的 cursor / windsurf entry 走 `entry.target = 'cursorrules' / 'windsurfrules'` 复制规则文件（不是 SKILL.md），跟 claude/codex 的 SKILL.md 复制路径不同——已在 AGENTS.md / HOST_COMPATIBILITY.md 说明。

## 总结

- **3 个 producer 任务全部 PASS**：适配器 + .harness 核心 + .harness 自动化
- **3 个真问题在 cycle 内被发现并由 owner 修干净**：版本号 / 能力提及 / trae 适配
- **4 个一致性 warn 全部清零**：output_artifacts / prompts / distribution ↔ manifest
- **最终全绿**：5 个 audit/检查全 PASS，0 FAIL 0 WARN
