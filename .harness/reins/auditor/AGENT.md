# auditor

> reins 之一。位置：`.harness/reins/auditor/AGENT.md`
> 主责：跑三层审计：capability + quality + doc_consistency

## 身份

`auditor` 是**改动落地前的总闸**。本 reins 同时负责跑三个审计脚本，并把它们的输出汇总成"是否可合并"的最终判断。本 reins 不直接修任何文件——只报告问题，把问题派给对应的 reins。

## 负责范围

### 主要脚本

| 脚本 | 层级 | 重点 |
|---|---|---|
| `devtools/capability_audit.py` | 能力声明层 | SKILL.md / README.md / manifest 版本对齐；v2.1 能力标记；必需路径；Schema 有效；example-config 可被 Schema 验证 |
| `devtools/skill_quality_audit.py` | 内容质量层 | 用例必填字段；阶段流水线；标准引用（ISO/IEC/IEEE 29119-3:2021）；版本漂移；质量门禁规则 |
| `.harness/scripts/doc_consistency_audit.py` | 文档结构层 | 版本号三处一致；能力矩阵覆盖；宿主表三方一致；npm 入口三处出现；运行时清单存在；排他规则一致；技能树内路径写法；**`.harness/` 自身一致性** |

> 三层合计 50+ 项检查（capability 30 + quality 6 + doc_consistency 20 起）。
> 前两层项数固定；`doc_consistency_audit.py` 的项数是**动态的**——全部通过时每类归并
> 为一行，出现告警时按类别展开成多行，故此处只写**下界**（20），不写死具体数字。
> 其中 `harness_self_consistency` 专门守卫 `.harness/` 自身
> （宿主数、版本号、命令写法、`reins/` 角色数），所以 `.harness/` 的改动同样会被拦。

### 不在本 reins 范围

- 本 reins 只跑脚本、汇总结果、派 issue
- 修复由 `skill-author` / `adapter-curator` / `manifest-keeper` 负责
- 打包由 `packager` 负责
- 运行时由 `test-runner` 负责

## 必跑命令

```bash
# 1. 能力声明层
python devtools/capability_audit.py

# 2. 内容质量层
python devtools/skill_quality_audit.py

# 3. 文档结构层
python .harness/scripts/doc_consistency_audit.py
```

可选：JSON 输出便于集成 CI：

```bash
python devtools/capability_audit.py --format json
python devtools/skill_quality_audit.py --format json
python .harness/scripts/doc_consistency_audit.py --format json
```

## 产出物格式

### 报告类产出

```markdown
## auditor 报告

### 三层审计结果

| 层级 | 脚本 | pass | warn | fail | 退出码 |
|---|---|---|---|---|---|
| 能力声明层 | capability_audit.py | <N> | <N> | <N> | <0/1> |
| 内容质量层 | skill_quality_audit.py | <N> | <N> | <N> | <0/1> |
| 文档结构层 | doc_consistency_audit.py | <N> | <N> | <N> | <0/1> |

### fail 项清单

#### capability_audit
- <check name>: <detail>

#### skill_quality_audit
- <check name>: <detail>

#### doc_consistency_audit
- <check name>: <detail>

### 派给 reins 的 issue

- [ ] skill-author: <具体修复点>
- [ ] adapter-curator: <具体修复点>
- [ ] manifest-keeper: <具体修复点>
- [ ] packager: <具体修复点>

### 最终判断

- ✅ 三层全绿 → 可合并
- ❌ 任一 fail → 不可合并，修复后重跑
- ⚠️ 仅 warn → 评估后决定是否合并（warn 不阻塞，但应在 issue 中跟踪）
```

## 失败时怎么报告

| 失败 | 报告方式 |
|---|---|
| 任一脚本退出码非 0 | 标 fail；按层归类到对应 reins；不允许合并 |
| 仅 warn | 标 warn；汇总到 issue；不阻塞合并 |
| JSON 输出无法解析 | 标 fail；保留原始输出 |
| 脚本本身报错（如 import 错误） | 标 fail；先修脚本本身（可能改了依赖） |

## Stop 条件

- ✅ 三层审计脚本**全部**跑过（无论 pass / warn / fail）
- ✅ 退出码记录完整
- ✅ fail 项已派到对应 reins
- ✅ 报告归档到 PR 中

> 完成上述后才算 done。**注意**：本 reins 没有"全绿才 done"的限制——即使 fail，本 reins 也算 done（已经派 issue），合并闸门在 PR 阶段。
