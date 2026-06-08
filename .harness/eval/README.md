# .harness/eval/ — 离线端到端 eval 流水线

本目录提供 `testcase-generator` Skill 的**离线**回归流水线。它不调
LLM、不连网络，只回答三个问题：

1. 每个 `test-fixtures/skill-eval/` 里的样本文件，phase0-5 的提示词
   是否都覆盖了对应的输入类型？
2. `SKILL.md` / `skill.manifest.json` 是否声明了处理该类型的能力？
3. 对每个 fixture 期望的产物路径，是否在 `test-output/` 里出现过？

跑分结果在 CI 入口与本地均可重现。

## 文件清单

| 文件 | 作用 |
|---|---|
| `run_eval.py` | 离线 eval 主入口 |
| `EXPECTED_OUTPUTS.md` | 每个 fixture → 期望产物的对应表 |
| `baselines/README.md` | 基线来源与已选子集说明 |
| `HEALTH_REPORT.md` | （由 final-verification 任务写入的整体验证报告） |

## 用法

```bash
# 默认输出 markdown 报告
python .harness/eval/run_eval.py

# JSON 输出（CI 友好）
python .harness/eval/run_eval.py --format=json

# 同时把报告写到文件
python .harness/eval/run_eval.py --output=.harness/eval/last-run.md

# warn 也算 fail（CI 严格门禁）
python .harness/eval/run_eval.py --strict
```

退出码：

- `0` — 全部 pass（warn 在非 strict 模式下不阻断）
- `1` — 至少一个 fail，或 `--strict` 模式下有 warn
- `2` — eval 自身跑不起来（fixture 目录不存在等）

## 检查维度

### 1. Prompt 覆盖（每个 fixture）

对 `prompts/phase0..phase5_prompt.md` 六个文件做大小写不敏感的关键词
扫描。每个 fixture 在 `run_eval.py` 的注册表里登记了 `input_kinds` 列
表（如 `login_prd.md` 登记 `prd / 需求文档 / 用户故事 / 用例`）。
如果某个 phase 的 prompt 完全没提到这些 token，会报 `warn`——表示
该 phase 还没意识到这个输入类型。

> 这是 `warn` 而非 `fail`，因为 MBT / 代码分析等阶段可能对部分输入类
> 型没有强语义（例：纯 API YAML 不需要 Phase 4 重新跑一遍状态建模）。
> 把它当 backlog 信号：让对应 rewire 的 reins 去补相关提示词。

### 2. Capability 覆盖（每个 fixture）

`SKILL.md` + `skill.manifest.json` + `README.md` 三处必须包含
fixture 登记的 `capability_tokens`（如 `根据 API 规范生成接口测试
场景`）。任何缺失都是 `fail`，因为这是 `AGENTS.md` §4.5 「能力
矩阵不能分叉铁律」的具体落地。

### 3. 期望产物路径（每个 fixture）

每个 fixture 在 `EXPECTED_OUTPUTS.md` 中显式登记了若干相对 `test-output/`
的产物路径（如 `phase1/01_requirements_summary.md`）。Eval 流水线
会去 `test-output/` 下检查这些文件是否真的存在过——`pass` 表示全
部已生成，`warn` 表示部分存在，`fail` 表示一个都没生成。

> 注意：`test-output/` 是本地验证产物，**不入包**。eval 流水线读它
> 是因为我们用过去的运行结果做基线。如果 `test-output/` 整个被清空，
> 全部 fixture 的 `expected_outputs` 检查会变 `warn`/`fail`——这时
> 需要重新跑一次 Skill 生成基线，或更新 `EXPECTED_OUTPUTS.md` 标记
> 该路径为「期望但暂未生成」。

### 4. Phase 0 阈值文档化（全局）

`EXPECTED_OUTPUTS.md` 标注 Phase 0 的输入质量评分 ≥ 80 分。Eval 会
在 `README.md` / `.harness/AGENTS.md` / `prompts/phase0_*.md` /
`resources/quality_checklist.md` 中扫这个阈值是否被明文声明。如果
没有，全局 `warn`——`AGENTS.md` §3 要求所有"必跑命令"的阈值都明确。

## 离线保证

`run_eval.py` 全文搜索：

- 不 `import requests` / `urllib` / `httpx` / `socket`
- 不打开任何 `http://` / `https://` 链接
- 不读 `~/.npm` / `~/.cache` 等用户目录
- 不 spawn 任何 LLM CLI

只读：

- `test-fixtures/skill-eval/` 的 fixture 文件
- `prompts/phase*.md`
- `SKILL.md` / `README.md` / `skill.manifest.json` / `.harness/AGENTS.md`
- `test-output/`（可选）

这意味着 eval 可以在 CI 的离线 runner 上跑，也可以在断网笔记本上跑。

## 注册新 fixture

把样本放到 `test-fixtures/skill-eval/<name>.<ext>`，然后在
`run_eval.py` 的 `build_fixture_registry()` 中追加一个 `FixtureSpec`
条目（input_kinds / capability_tokens / expected_outputs），并在
`EXPECTED_OUTPUTS.md` 里登记期望产物。两条规则：

1. 名称必须稳定——一旦登记就**不要重命名**，否则会破坏历史基线。
2. 期望产物路径使用相对 `test-output/` 的 POSIX 风格（`phase1/01_*.md`）。

## 与其他工具的关系

- **`devtools/capability_audit.py`**：声明层审计（Schema、必需路径、
  版本对齐）。`run_eval.py` 不重复它，专注于「fixture ↔ 能力 ↔
  产物」三角。
- **`devtools/skill_quality_audit.py`**：内容层审计（必填字段、质量
  token、标准引用）。`run_eval.py` 不重复。
- **`.harness/scripts/doc_consistency_audit.py`**：结构层审计（版本
  号、能力、宿主表三方一致）。`run_eval.py` 不重复。

这三个 + `run_eval.py` 合起来，就是 `.harness/AGENTS.md` §3「必跑
命令」中所有 audit 的完整覆盖。
