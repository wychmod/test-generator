# .harness/ 体系总览

> 位置：`.harness/README.md`
> 范围：仅对 `D:\pycharm\test-generator` 仓库生效
> 语言：中文优先

`.harness/` 是本仓库的 **AI 协作操作系统**：让 AI agent 像有"宪法 + 角色 + 护栏"一样稳定地改动本仓库。

## 为什么需要 .harness

`testcase-generator` 是一个 **Skill 包**（不是普通库），有非常具体的：

- **入包边界**（什么能进 `.skill` / `.zip`，什么不能 —— manifest「分发排除」当前 48 项）
- **多宿主适配**（**26 个宿主**，清单见 `HOST_COMPATIBILITY.md`）
- **四层审计**（能力声明层 / 内容质量层 / 文档结构层 / 端到端评测）
- **方法论铁律**（MBT + 六阶段流水线，能力矩阵不能分叉）

没有 `.harness/`，每次 AI 改动都靠 prompt 提醒，容易漏；有了 `.harness/`，所有 AI 协作都从读项目宪法开始，按 reins 角色分工跑命令验证。

> **单一数据源原则**：本目录的一切"事实"（版本号、宿主数、reins 清单、分发排除）
> 都不得自行维护，必须以 `skill.manifest.json` / `lib/activation.js` / `adapters/` 为准。
> `doc_consistency_audit.py` 的 `harness_self_consistency` 检查会拦住漂移。

## 文件结构

```text
.harness/
├── AGENTS.md                           # 项目宪法（本仓库所有 AI 协作的最高准则）
├── README.md                           # 本文件：.harness 体系总览
├── reins/                              # AI 协作角色团队（6 个）
│   ├── README.md                       # reins 角色索引 + 新增 reins 流程
│   ├── skill-author/AGENT.md           # SKILL.md / prompts / templates / resources 维护
│   ├── adapter-curator/AGENT.md        # adapters/ 多宿主薄适配维护
│   ├── manifest-keeper/AGENT.md        # skill.manifest.json + DISTRIBUTION.md 一致性
│   ├── packager/AGENT.md               # 跑 package_skill.py + 验证 .skill / .zip 一致
│   ├── auditor/AGENT.md                # 跑三层审计（capability / quality / doc_consistency）
│   └── test-runner/AGENT.md            # 跑 npm test / test:python / run_eval.py + 验证宿主激活路径
├── scripts/
│   ├── README.md                       # 护栏脚本使用说明
│   └── doc_consistency_audit.py        # 文档结构层护栏（可独立运行，CI required check）
├── eval/                               # 端到端离线评测流水线
│   ├── README.md                       # 评测说明
│   ├── run_eval.py                     # 基线 fixture → 校验提示词覆盖与产物路径
│   ├── EXPECTED_OUTPUTS.md             # 预期产物清单
│   ├── HEALTH_REPORT.md                # 历史时点验证报告（v2.1.0 期，不参与一致性校验）
│   └── baselines/                      # 回归基线
└── changelogs/                         # 发版日志
    ├── README.md                       # 规范说明
    ├── v2.1.0.md / v2.2.0.md           # 已发布版本
    ├── v2.3.0.md                       # 当前版本
    └── v2.4.0-TEMPLATE.md              # 下一版模板
```

> 已移除 `hooks/`：其 pre-commit / pre-package 钩子在引入后**从未安装**
> （`.git/hooks/` 中只有被改名的 `pre-commit.disabled`，`core.hooksPath` 也未配置），
> 且 CI 已完整承担同等职责，属纯冗余。

## 跟项目根 AGENTS.md 的分工

本仓库有**两个 AGENTS.md**，职责刻意分离：

| 文件 | 角色 | 读者 | 约束 |
|---|---|---|---|
| [`AGENTS.md`](../AGENTS.md)（仓库根） | 仓库操作说明：项目身份一句话、必跑命令、与生态默认不同的约定、边界、已踩过的坑 | **所有 AI agent**（20+ 工具每会话自动注入） | **必须 ≤100 行**——过长会实测降低 agent 表现 |
| [`.harness/AGENTS.md`](./AGENTS.md)（本目录） | 完整项目宪法：目录速查表、7 条协作铁律、PR 模板、失败升级路径、reins 角色索引 | reins 与需要完整规则的协作者 | 可长，按需阅读 |

**根 `AGENTS.md` 于 v2.3.0 补齐**（此前长期只有 `.harness/AGENTS.md` 承担宪法角色）。
分工原则：**能被 agent 自行推断的内容不写进根文件**；根文件只放"agent 无法推断"的硬约束，
其余用一行指向本目录。

## 各子目录索引

- **`.harness/AGENTS.md`** — 项目宪法。从这里开始读。
- **`.harness/reins/`** — 6 个 reins 角色团队。详见 [`.harness/reins/README.md`](./reins/README.md)。
- **`.harness/scripts/`** — 文档护栏脚本。详见 [`.harness/scripts/README.md`](./scripts/README.md)。
- **`.harness/eval/`** — 端到端评测流水线。详见 [`.harness/eval/README.md`](./eval/README.md)。
- **`.harness/changelogs/`** — 发版日志。详见 [`.harness/changelogs/README.md`](./changelogs/README.md)。

## 跑一次完整审计

```bash
# 1. 能力声明层
python devtools/capability_audit.py

# 2. 内容质量层
python devtools/skill_quality_audit.py

# 3. 文档结构层（含 .harness/ 自身一致性）
python .harness/scripts/doc_consistency_audit.py

# 4. 端到端评测
python .harness/eval/run_eval.py

# 5. 单测（显式文件列表，勿写成 glob）
npm test
npm run test:python
```

**四层审计 + 两套单测全绿 → 改动可合并。** 前四项与单测均为 CI required check。

## 添加新的 reins

1. 在 `.harness/reins/` 下新建 `<name>/` 目录
2. 写 `<name>/AGENT.md`，按现有 reins 的格式（身份 / 范围 / 必跑命令 / 产出物 / 失败报告 / Stop 条件）
3. 在 `.harness/reins/README.md` 的角色清单中加一行
4. 在 `.harness/AGENTS.md` 的 reins 角色索引表中加一行
5. 在 `.harness/AGENTS.md` 的"必跑命令"表中加 reins 跑的命令（如有）
6. 跑 `.harness/scripts/doc_consistency_audit.py` 验证不会破坏现有规则
