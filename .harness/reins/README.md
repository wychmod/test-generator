# reins 角色索引

> 位置：`.harness/reins/README.md`
> 范围：6 个 reins 角色团队，所有 AI 协作 agent 在改动本仓库前必须先读本文件

## reins 是什么

"reins" = reins agent。本仓库的 reins 是**专门化的 AI 协作角色**，每个 reins 对应仓库内的一类改动和一类必跑命令。reins 通过**文件改动 + 跑命令验证**的方式工作，不通过 chat 互调。

## 6 个 reins 速查

| reins | 一句话身份 | 必跑命令 |
|---|---|---|
| [`skill-author`](./skill-author/AGENT.md) | 维护 `skills/testcase-generator/` 下的 SKILL.md / prompts/ / templates/ / resources/ / references/，把方法论铁律写进内容 | `python devtools/capability_audit.py` / `python devtools/skill_quality_audit.py` |
| [`adapter-curator`](./adapter-curator/AGENT.md) | 维护 adapters/ 薄适配层（26 宿主），确保与技能树 SKILL.md + 触发场景同步 | `python .harness/scripts/doc_consistency_audit.py` |
| [`manifest-keeper`](./manifest-keeper/AGENT.md) | 维护 skill.manifest.json + DISTRIBUTION.md 一致性 | `python .harness/scripts/doc_consistency_audit.py` |
| [`packager`](./packager/AGENT.md) | 跑 package_skill.py，验证 .skill / .zip 一致 | `python devtools/package_skill.py` |
| [`auditor`](./auditor/AGENT.md) | 跑三层审计：capability + quality + doc_consistency | `python devtools/capability_audit.py` / `python devtools/skill_quality_audit.py` / `python .harness/scripts/doc_consistency_audit.py` |
| [`test-runner`](./test-runner/AGENT.md) | 跑 `npm test` / `npm run test:python` / `run_eval.py`，验证 lib/activation.js 在所有宿主下激活路径正确 | `npm test` / `npm run test:python` / `python .harness/eval/run_eval.py` |

## reins 的协作模式

```text
            ┌──────────────────┐
            │  auditor (总闸)  │  ← 先跑三层审计，知道哪个 reins 负责修
            └────────┬─────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
 skill-author  adapter-curator  manifest-keeper
 (内容层)        (薄适配层)      (分发层)
       │             │             │
       └─────────────┼─────────────┘
                     ▼
              ┌────────────┐
              │  packager  │  ← 打包验证
              └────────────┘
                     │
                     ▼
            ┌────────────────┐
            │  test-runner   │  ← 运行时验证
            └────────────────┘
```

实际工作时：
1. 改代码或文档前，**先读 `.harness/AGENTS.md` 再读对应 reins 的 `AGENT.md`**
2. 改完后**只跑自己 reins 的必跑命令**
3. 跨 reins 的改动（如改了 SKILL.md + adapters + manifest），由 PR 模板串联所有验证
4. 任何 reins 发现自己范围外的问题，写入对应 reins 的 issue 清单，不擅自越界

## 每个 reins 的 AGENT.md 结构

每个 reins 的 `AGENT.md` 都按以下 6 段写：

1. **身份** — 一两句话讲清楚这个 agent 是干嘛的
2. **负责范围** — 具体文件 / 目录
3. **必跑命令** — 该角色常跑的命令（含具体参数）
4. **产出物格式** — 报告 / 改动 / 验证结果 怎么写
5. **失败时怎么报告** — 哪些情况算 fail / 怎么写 issue
6. **Stop 条件** — 什么时候算 done

## 怎么新增 reins

参考 `.harness/README.md` 中的"添加新的 reins"段落。要点：

1. 在 `.harness/reins/<name>/AGENT.md` 写好 6 段
2. 更新 `.harness/reins/README.md`（本文件）的速查表
3. 更新 `.harness/AGENTS.md` 的 reins 角色索引表
4. 跑 `.harness/scripts/doc_consistency_audit.py` 验证

新增 reins 时**不要**：
- 把 reins 名加到 `skill.manifest.json` 的"运行时文件"中（reins 是开发元数据，不是运行时资产）
- 改 `package.json` 的 `files` 字段
- 在分发脚本（`devtools/package_skill.py`）的 `STATIC_EXCLUDES` 中显式列出 reins 目录（`.harness/` 自然被排除规则排除——见 4.1 入包边界铁律）

## reins 优先级

如果多个 reins 都要改，按以下优先级：

1. **manifest-keeper** 优先于 skill-author（manifest 定义什么能入包）
2. **adapter-curator** 依赖 manifest-keeper（adapter 引用 manifest 里的宿主入口）
3. **packager** 必须在 manifest 改完后跑
4. **auditor** 必须在所有改动完后跑
5. **test-runner** 在涉及 `lib/activation.js` / `bin/test-generator.js` / `prompts/` / `templates/` 时跑

## 关于 reins 的常见误解

**「`reins/` 没有任何脚本引用，是不是死代码？」** —— 不是。

reins 是**人/AI 协作角色契约**，不是可执行程序。按 `.harness/AGENTS.md` §4.7：
> reins 之间通过**文件改动 + 跑命令验证**的方式协作，不通过 chat 互调。

因此"零脚本引用"是**设计使然**。判断一个 reins 是否有价值，看的是：
① 它是否对应一类真实改动；② 它是否有独立的必跑命令；③ 它是否有唯一负责的文件集。

反过来，真正该警惕的是**内容过期**——`.harness/` 长期不在审计覆盖内，
所以 `reins/*/AGENT.md` 里的宿主数、命令写法、文件清单曾整体停留在 v2.2.0 时代。
现已由 `doc_consistency_audit.py` 的 `harness_self_consistency` 检查纳入守卫。
