# 文档护栏脚本

> 位置：`.harness/scripts/`
> 主责：跑文档结构层的一致性检查

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `doc_consistency_audit.py` | 12 类文档一致性检查（版本号 / 能力矩阵 / 宿主表 / npm 入口 / 运行时清单 / 排他规则 / changelog / docs 路径 / docs 链接 / npm 载荷 / 技能树路径 / `.harness/` 自身） |

## doc_consistency_audit.py

### 执行 12 类检查

| # | 检查项 | 失败影响 | 谁来修 |
|---|---|---|---|
| 1 | **版本号三处一致**（SKILL.md front matter / README.md 标题 / skill.manifest.json "版本"） | 必须修，否则 `fail` | skill-author + manifest-keeper |
| 2 | **能力矩阵覆盖**（manifest.核心能力 ↔ SKILL.md ↔ prompts/phase*.md ↔ resources/output_artifacts.md） | `fail`：核心能力未在 SKILL.md 出现 | skill-author |
| 3 | **宿主表三方一致**（HOST_COMPATIBILITY.md ↔ adapters/ 实际目录 ↔ lib/activation.js 的 ENVIRONMENTS） | `fail`：缺入口或缺注册 | adapter-curator + test-runner |
| 4 | **npm 脚本入口**（test-generator 在 README / package.json / HOST_COMPATIBILITY 都有提到） | `fail`：三处缺一不可 | manifest-keeper |
| 5 | **运行时分发清单**（manifest.运行时文件 实际都存在） | `fail`：清单中的文件/目录不存在 | manifest-keeper |
| 6 | **排他规则一致性**（DISTRIBUTION.md 建议排除/开发工具 ↔ manifest.分发排除 ↔ devtools/package_skill.py 的 STATIC_EXCLUDES + FORBIDDEN_ARCHIVE_PATTERNS） | `fail`：关键禁入项未声明 | manifest-keeper + packager |
| 7 | **版本↔changelog**（当前版本必须有正式 changelog，不能只留模板） | `fail`：发版日志未回填 | 发版人 |
| 8 | **docs/ 技能树路径**（docs/ 引用技能内容必须带 `skills/testcase-generator/` 前缀） | `fail`：路径写法失效 | 改 docs/ 的人 |
| 9 | **docs/ 相对链接**（docs/ 下的 Markdown 相对链接必须可解析） | `fail`：死链 | 改 docs/ 的人 |
| 10 | **npm 发布载荷**（package.json 的 files 目录条目不得牵连被 gitignore 的内容） | `fail`：会静默发布本地/生成物 | manifest-keeper |
| 11 | **技能树内路径写法**（技能树文档引用顶层目录必须带 `<技能根>/` 前缀） | `fail`：跨深度相对路径歧义 | skill-author |
| 12 | **`.harness/` 自身一致性**（宿主数 / reins 数 / 分发排除项数 vs 仓库现状；不得引用已删除目录） | `fail`：治理文档与现实脱节 | 对应 reins |

> 第 12 项是为纪念一类真实事故：`.harness/` 是护栏脚本的**所在处**，却长期恰好落在
> 自己的审计辖区之外 —— 于是 `reins/*/AGENT.md` 里的宿主数、命令写法、文件清单
> 整体停留在 v2.2.0 时代而无人报警。与 `docs/` 曾经的盲区是同一个病：
> **裁判席不在自己辖区里**。
>
> 判定是零猜测的：数字先与"仓库现状"（真实目录数、真实数组长度）比对；历史记录
> （`.harness/changelogs/`、`.harness/eval/baselines/`、`.harness/eval/HEALTH_REPORT.md`）
> 被排除在扫描范围之外，因此"过去某一版的正确记录"不会被误判为漂移。

### 用法

```bash
# 默认输出 markdown 报告
python .harness/scripts/doc_consistency_audit.py

# 输出 JSON（便于 CI 集成）
python .harness/scripts/doc_consistency_audit.py --format json

# 查看帮助
python .harness/scripts/doc_consistency_audit.py --help
```

### 退出码

- `0`：没有 fail（可以有 warn）
- `1`：至少一个 fail

### 在 PR 流程中

每次 PR 之前**必须**跑本脚本，全绿才能合并：

```bash
# 完整四层审计
python devtools/capability_audit.py
python devtools/skill_quality_audit.py
python .harness/scripts/doc_consistency_audit.py
python .harness/eval/run_eval.py
```

### 输出示例

```text
# 文档一致性审计报告 (doc_consistency_audit)

- 仓库根目录：`D:\pycharm\test-generator`
- 报告时间：由 doc_consistency_audit.py 实时生成

| Check | Status | Detail |
| --- | --- | --- |
| version_alignment | pass | 三处版本号一致：2.3.0 |
| changelog_exists | pass | v2.3.0 的正式 changelog 已回填（.harness/changelogs/v2.3.0.md） |
| harness_host_count | pass | .harness/ 中宿主数声称均与 ENVIRONMENTS 一致（26 个） |
| ... | ... | ... |

- Passed: 20
- Warned: 0
- Failed: 0
```

### 不修改任何文件

本脚本**只读**，不修改任何项目文件。修复时按 fail / warn 列表交给对应 reins。

### 适用范围

- 当前仓库根：`D:\pycharm\test-generator`
- 自动以脚本所在位置向上两级定位仓库根
- 不接受 `--root` 参数（避免误用）

## 与其他护栏脚本的关系

```text
devtools/capability_audit.py      →  能力声明层（必需文件、版本对齐、Schema）
devtools/skill_quality_audit.py   →  内容质量层（必填字段、阶段流水线、标准引用）
.harness/scripts/
  doc_consistency_audit.py        →  文档结构层（含 .harness/ 自身一致性）
.harness/eval/
  run_eval.py                     →  端到端层（fixture → 能力 → 产物）
```

四层全绿 → 改动可合并。
