# 贡献指南

> 目的：让外部贡献者和未来的自己能够一致地修改、扩展 testcase-generator，并保证所有改动都不会破坏 Skill 的可分发性。
>
> 本 Skill 的特殊性：**分发包是产物的产物**——你修改源代码的同时，必须考虑它如何被打包到 `.skill` / `.zip` / npm，以及如何被各个 AI 宿主识别。
>
> 相关：[`adding-host-adapter.md`](adding-host-adapter.md)（新增宿主适配器）/ [`../../DISTRIBUTION.md`](../../DISTRIBUTION.md)（分发边界）/ [`../../.harness/AGENTS.md`](../../.harness/AGENTS.md)（团队 reins 体系）

---

## 1. 改之前的 5 个问题

开始任何改动前，回答这 5 个问题：

1. **改的是哪个能力？** 对应 `skill.manifest.json` 中的 7 项核心能力之一吗？
2. **是否影响分发包？** 改完后的产物能正确进入 `.skill` / `.zip` / npm 吗？
3. **是否影响宿主适配？** 改动会被 8 个适配器中的哪些发现？
4. **是否有回归保护？** `.harness/eval/baselines/` 下的基线用例是否同步更新？
5. **是否更新文档？** 涉及 SKILL.md / README.md / DISTRIBUTION.md 哪几个？

任何一个回答为"不知道"，先停下来调研；任何一个回答为"否"，需要解释为什么可以不做。

---

## 2. 工作流

```
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │  1. 提 Issue  │    │  2. Fork +   │    │  3. 改 + 自测  │    │  4. PR       │
  │              │ ─► │     分支      │ ─► │              │ ─► │              │
  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │  5. Review   │
                                                          │  + Merge     │
                                                          └──────────────┘
```

### Step 1：提 Issue（可选但推荐）

- Bug 报告：触发条件、复现步骤、预期与实际
- 功能请求：场景描述、为什么现有能力不够、建议方案
- 改动涉及 7 项核心能力 → 标 `core-capability-change`

### Step 2：Fork + 分支

分支命名规范：

| 类别 | 前缀 | 示例 |
|---|---|---|
| 新能力 | `feat/` | `feat/phase3-event-storming` |
| Bug 修复 | `fix/` | `fix/audit-missing-prompt-check` |
| 重构 | `refactor/` | `refactor/activation-js-modularize` |
| 文档 | `docs/` | `docs/pipeline-overview` |
| 测试 | `test/` | `test/quality-gate-coverage` |
| 发布 | `release/` | `release/v2.2.0` |

### Step 3：改 + 自测

按改动类型执行对应的检查（见 §3）。

### Step 4：PR

PR 标题规范：`{type}: {一句话描述}`（与 commit message 第一行一致）。

PR 描述必须包含：

```
## 改了什么
- bullet 1
- bullet 2

## 为什么
- 关联 Issue: #NNN（若无，留空）
- 业务场景或问题描述

## 校验
- [ ] capability_audit.py 通过
- [ ] node --test test/ 通过
- [ ] python -m pytest test/ 通过
- [ ] python devtools/package_skill.py 通过
- [ ] 涉及 prompts 时，eval/baselines/ 同步更新
- [ ] 涉及 manifest 时，DISTRIBUTION.md / HOST_COMPATIBILITY.md 同步更新
- [ ] SKILL.md / README.md 顶部声明若受影响已同步
```

### Step 5：Review + Merge

维护者会按 §5 的清单 review。review 通过后才能 squash merge 到 `main`。

---

## 3. 按改动类型的检查清单

### 3.1 改 `prompts/phaseN_*.md`

| # | 检查项 | 命令 / 工具 |
|---|---|---|
| 1 | capability_audit 仍能找到 7 项核心能力 | `python devtools/capability_audit.py` |
| 2 | 顶部 YAML 元数据齐全（版本、阶段目标、输入来源、输出去向、对应核心能力） | 人工 review |
| 3 | 后续阶段的 prompt 仍引用上一阶段的产物 ID | grep |
| 4 | 测试基线 `.harness/eval/baselines/` 同步更新 | `python .harness/eval/run_eval.py` |
| 5 | `resources/output_artifacts.md` 中对应阶段产物列表仍然准确 | 人工 review |

### 3.2 改 `templates/*.md` 或 `resources/*.md`

| # | 检查项 |
|---|---|
| 1 | 模板字段命名未被下游 prompt 硬编码（破坏一致性） |
| 2 | `SKILL.md` 中对模板的引用仍然成立 |
| 3 | 静态审计 `devtools/skill_quality_audit.py` 通过 |

### 3.3 改 `adapters/<host>/`

详见 [`adding-host-adapter.md`](adding-host-adapter.md)。新增 vs 修改有不同流程。

### 3.4 改 `skill.manifest.json`

| # | 检查项 |
|---|---|
| 1 | 7 项核心能力字段未减少（可增加） |
| 2 | `运行时文件` 与 `分发排除` 互斥且穷尽 |
| 3 | `宿主适配入口` 中所有 host 在 `adapters/` 下都有对应目录 |
| 4 | `入口文件` 路径在根目录 |
| 5 | `DISTRIBUTION.md` 已同步更新 |
| 6 | `HOST_COMPATIBILITY.md` 已同步更新（如改适配器） |
| 7 | `devtools/package_skill.py` 仍能产出有效 `.skill` / `.zip` |

### 3.5 改 `SKILL.md` / `README.md` / `DISTRIBUTION.md` / `HOST_COMPATIBILITY.md`

| # | 检查项 |
|---|---|
| 1 | 这 4 份保留在根目录（不可移动） |
| 2 | 内部链接使用相对路径 |
| 3 | 顶部 YAML frontmatter（仅 SKILL.md）字段完整 |
| 4 | 中文为主，术语与 `skill.manifest.json` 一致 |
| 5 | `node --test test/activation.test.js` 通过（测试会校验这 4 份的存在） |

### 3.6 改 `devtools/*.py`

| # | 检查项 |
|---|---|
| 1 | `python -m pytest test/` 通过 |
| 2 | `python devtools/capability_audit.py` 通过 |
| 3 | `python devtools/package_skill.py` 成功生成两个产物 |
| 4 | 双产物 `.skill` 与 `.zip` namelist 完全一致 |
| 5 | 必需文件（SKILL.md / README.md / DISTRIBUTION.md / manifest）入包 |

### 3.7 改 `bin/*.js` / `lib/*.js`

| # | 检查项 |
|---|---|
| 1 | `node --test test/activation.test.js` 通过 |
| 2 | `package.json` 中 `files` 与 `bin` 仍正确 |
| 3 | `test-generator activate <env> --dry-run` 行为正确 |

### 3.8 改 `package.json`

| # | 检查项 |
|---|---|
| 1 | `files` 字段涵盖所有运行时分发资产 |
| 2 | `bin` 字段 CLI 入口路径正确 |
| 3 | 版本号与 `SKILL.md` frontmatter 和 `skill.manifest.json` 同步 |
| 4 | `npm test` 通过 |
| 5 | `npm pack --dry-run` 列出的文件与 `.skill` 一致 |

### 3.9 改 `docs/`

| # | 检查项 |
|---|---|
| 1 | 相对路径链接在 GitHub 渲染下正常 |
| 2 | 没有"野文件目录"（每个子目录都有 README.md） |
| 3 | 不复制 `../SKILL.md` / `../DISTRIBUTION.md` / `../HOST_COMPATIBILITY.md` 的全部内容 |
| 4 | 改动 changelog 入口 |

---

## 4. 测试策略

### 4.1 单元测试

| 范围 | 工具 | 位置 |
|---|---|---|
| Node.js 激活逻辑 | `node:test` | `test/activation.test.js` |
| Python 工具链 | `pytest` | `test/test_skill_quality_audit.py` |

### 4.2 端到端评测

`python .harness/eval/run_eval.py` — 跑基线输入过完六阶段，对比评分。

### 4.3 文档一致性审计

`python .harness/scripts/doc_consistency_audit.py` — 检查 SKILL.md / package.json / skill.manifest.json 的版本号、产物清单、能力声明是否一致。

### 4.4 何时该加测试

| 改动 | 必须加测试 |
|---|---|
| 修改 `devtools/*.py` 的核心逻辑 | 单元测试 |
| 修改 `bin/test-generator.js` 或 `lib/activation.js` | 单元测试 |
| 修改 `prompts/phaseN` 的输出结构 | eval/baselines/ 加新基线 |
| 修改 `templates/*.md` 字段 | eval/baselines/ 加新基线 |

---

## 5. Code Review 清单

reviewer 必须逐项确认：

### 5.1 分发完整性

- [ ] `python devtools/capability_audit.py` 21/21 通过
- [ ] `python devtools/package_skill.py` 成功生成 `.skill` 和 `.zip`，双产物一致
- [ ] `git ls-files` 没有把不该跟踪的文件带入索引（参考 `.gitignore`）

### 5.2 测试通过

- [ ] `python -m pytest test/` 5/5 通过
- [ ] `node --test test/activation.test.js` 7/7 通过
- [ ] 若改了 prompts / templates：`python .harness/eval/run_eval.py` 不退化

### 5.3 文档同步

- [ ] 涉及核心能力 → `SKILL.md` + `skill.manifest.json` 同步
- [ ] 涉及适配器 → `HOST_COMPATIBILITY.md` + `lib/activation.js` + `package.json` `files` 同步
- [ ] 涉及打包边界 → `DISTRIBUTION.md` 同步
- [ ] 版本号变更 → `SKILL.md` frontmatter + `package.json` + `skill.manifest.json` 三处一致

### 5.4 安全与一致性

- [ ] 无硬编码密钥或敏感信息
- [ ] 中文文案与英文 manifest 表述一致
- [ ] 适配器入口文件名与宿主约定一致（claude/SKILL.md、codex/AGENTS.md、cursor/cursorrules.md 等）

### 5.5 git hygiene

- [ ] 提交信息遵循 `<type>: <subject>` 规范
- [ ] 一个 PR 只做一件事（或明确说明为什么要跨范围）
- [ ] 没有把调试用的 `console.log` / `print` 留在生产代码

---

## 6. 版本号规则

采用语义化版本（SemVer）：

```
MAJOR.MINOR.PATCH

MAJOR: 破坏性变更（如重命名适配器、删核心能力）
MINOR: 新增能力（如新增 phase、新增 adapter）
PATCH: 修复与文档更新
```

**三处必须同步**：
- `SKILL.md` 顶部 YAML：`version: X.Y.Z`
- `package.json`：`"version": "X.Y.Z"`
- `skill.manifest.json`：`"版本": "X.Y.Z"`

由 `.harness/scripts/doc_consistency_audit.py` 自动校验。

---

## 7. 发版流程

完整发版流程：

```
1. 确认 main 分支所有 PR 已合并、CI 全绿
2. 更新版本号（三处同步）
3. 在 docs/changelog/vX.Y.Z.md 写变更日志
4. 在 .harness/changelogs/vX.Y.Z.md 同步记录
5. python devtools/capability_audit.py
6. python devtools/package_skill.py（生成 .skill + .zip）
7. 手动验证：抽样打开 .skill 中每个 phase prompt，无乱码
8. npm publish（如果 npm 包有变更）
9. git tag vX.Y.Z && git push --tags
10. 在 GitHub 创建 Release，附 changelog 摘要
```

发版后任何 hotfix 必须从 main 拉分支，单独 PR 回 main。

---

## 8. 不接受的改动

- ❌ 把根目录 4 份 Markdown（SKILL.md / README.md / DISTRIBUTION.md / HOST_COMPATIBILITY.md）移到 `docs/`（会被 `package.json` `files`、`devtools/package_skill.py`、测试用例三处拒绝）
- ❌ 在 `prompts/` 下添加与 6 个阶段无关的新文件（破坏 capability_audit 的能力标记检索）
- ❌ 直接修改 `node_modules/` 内任何文件（应通过 `package.json` dependencies 升级）
- ❌ 把 `.opencode/` `.mavis/` `.workbuddy/` 目录的内容提交进仓库（已在 `.gitignore`）
- ❌ 在 `skill.manifest.json` 中删除 7 项核心能力中的任何一项
