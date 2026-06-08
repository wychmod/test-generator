# .harness/ 体系总览

> 位置：`.harness/README.md`
> 范围：仅对 `D:\pycharm\test-generator` 仓库生效
> 语言：中文优先

`.harness/` 是本仓库的 **AI 协作操作系统**：让 AI agent 像有"宪法 + 角色 + 护栏"一样稳定地改动本仓库。

## 为什么需要 .harness

`testcase-generator` 是一个 **Skill 包**（不是普通库），有非常具体的：

- **入包边界**（什么能进 `.skill` / `.zip`，什么不能）
- **多宿主适配**（claude / codex / qoder / openclaw / trae）
- **三层审计**（能力声明层 / 内容质量层 / 文档结构层）
- **方法论铁律**（MBT + 六阶段流水线，能力矩阵不能分叉）

没有 `.harness/`，每次 AI 改动都靠 prompt 提醒，容易漏；有了 `.harness/`，所有 AI 协作都从读项目宪法开始，按 reins 角色分工跑命令验证。

## 文件结构

```text
.harness/
├── AGENTS.md                           # 项目宪法（本仓库所有 AI 协作的最高准则）
├── README.md                           # 本文件：.harness 体系总览
├── reins/                              # AI 协作角色团队
│   ├── README.md                       # reins 角色索引 + 新增 reins 流程
│   ├── skill-author/AGENT.md           # SKILL.md / prompts / templates / resources 维护
│   ├── adapter-curator/AGENT.md        # adapters/ 多宿主薄适配维护
│   ├── manifest-keeper/AGENT.md        # skill.manifest.json + DISTRIBUTION.md 一致性
│   ├── packager/AGENT.md               # 跑 package_skill.py + 验证 .skill / .zip 一致
│   ├── auditor/AGENT.md                # 跑三层审计（capability / quality / doc_consistency）
│   └── test-runner/AGENT.md            # 跑 node --test test/ + 验证所有宿主激活路径
└── scripts/
    ├── README.md                       # 护栏脚本使用说明
    └── doc_consistency_audit.py        # 文档结构层护栏（可独立运行）
```

## 跟项目根 AGENTS.md 的关系

本仓库有**两个 AGENTS.md**：

| 文件 | 角色 | 读者 |
|---|---|---|
| `AGENTS.md`（项目根，如果存在） | 仓库级宪法，定义项目身份、目录速查、必跑命令、铁律 | 仓库内所有 AI agent |
| `.harness/AGENTS.md`（本目录） | `.harness` 体系的项目宪法，定义 reins、护栏、PR 模板、失败升级路径 | reins 和 AI 协作 agent |

**当前仓库根没有 `AGENTS.md`**，所以 `.harness/AGENTS.md` 同时承担了"项目宪法"的角色。

未来如果新增根 `AGENTS.md`，应该把"项目是什么 / 目录速查 / 必跑命令 / 铁律"上移到根 `AGENTS.md`，把"reins / 护栏 / PR 模板 / 失败升级"留在 `.harness/AGENTS.md`。

## 各子目录索引

- **`.harness/AGENTS.md`** — 项目宪法。从这里开始读。
- **`.harness/reins/`** — 6 个 reins 角色团队。详见 [`.harness/reins/README.md`](./reins/README.md)。
- **`.harness/scripts/`** — 文档护栏脚本。详见 [`.harness/scripts/README.md`](./scripts/README.md)。

## 跑一次完整审计

```bash
# 1. 能力声明层
python devtools/capability_audit.py

# 2. 内容质量层
python devtools/skill_quality_audit.py

# 3. 文档结构层
python .harness/scripts/doc_consistency_audit.py

# 4. 运行时层
node --test test/
node bin/test-generator.js environments
node bin/test-generator.js activate claude --dry-run
```

四层全绿 → 改动可合并。

## 添加新的 reins

1. 在 `.harness/reins/` 下新建 `<name>/` 目录
2. 写 `<name>/AGENT.md`，按现有 reins 的格式（身份 / 范围 / 必跑命令 / 产出物 / 失败报告 / Stop 条件）
3. 在 `.harness/reins/README.md` 的角色清单中加一行
4. 在 `.harness/AGENTS.md` 的 reins 角色索引表中加一行
5. 在 `.harness/AGENTS.md` 的"必跑命令"表中加 reins 跑的命令（如有）
6. 跑 `.harness/scripts/doc_consistency_audit.py` 验证不会破坏现有规则
