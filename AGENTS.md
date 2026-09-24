# AGENTS.md

面向 AI coding agent 的仓库操作说明。

**完整项目宪法见 [`.harness/AGENTS.md`](.harness/AGENTS.md)** —— 本文件刻意保持简短，因为它会在每次会话被注入上下文，过长会实测降低 agent 表现。这里只写 agent 无法自行推断的内容。

---

## 这是什么

`testcase-generator` 是一个 **Agent Skill 包**（不是普通库）：技能内容位于 **`skills/testcase-generator/`**（Agent Skills 标准布局，客户端可自动发现），`SKILL.md` 是中文主入口，`skill.manifest.json` 同时承担分发边界与版本契约。它为 8 个 AI 宿主提供触发式测试用例生成能力。

---

## 必跑命令

```bash
# 改过版本号 / 身份标记之后
python devtools/sync_version.py --write && python devtools/sync_version.py

# 改过 skill.manifest.json / package.json 之后
python devtools/gen_plugin_manifests.py --write

# 改过技能树内容（skills/ 下的 SKILL.md / prompts / references / resources / templates）之后
python devtools/capability_audit.py
python devtools/skill_quality_audit.py

# 改过技能入口 / README / manifest / adapters / HOST_COMPATIBILITY 之后
python .harness/scripts/doc_consistency_audit.py

# 改过 lib/activation.js 或 bin/ 之后
npm test          # node --test "test/**/*.test.js"
npm run test:python

# 发布前
python devtools/package_skill.py
```

前三项已在 CI 中作为 required check，本地也应先跑绿再提交。

---

## 与生态默认不同的约定（不要"顺手改正"）

- **版本的唯一数据源是 `skill.manifest.json` 的"版本"字段。** 不要手改技能树里的 `SKILL.md` / `prompts/` / `references/` / `resources/` / `templates/` 或外层 `README.md` 的版本号，跑 `sync_version.py --write` 回写。
- **`[v2.1 新增]` / `v2.1 增强内容` 是历史归属标记**，记录某能力是哪一版引入的，**禁止**随版本号一起改。
- **Postman / SARIF 外链里的 `v2.1.0` 不得改动**（那是外部规范 URL）。
- **`.claude-plugin/` 内只允许放 manifest**（`plugin.json` / `marketplace.json`），组件目录一律在插件根。该目录由 `gen_plugin_manifests.py` 生成，不要手改。
- **`adapters/<host>/` 是薄适配层**，只做入口文件名、触发词、资源路由、降级说明四件事；不得复制技能树 `skills/testcase-generator/` 下的实际内容，不得重新定义方法论。
- **中文优先**：`SKILL.md`、`.harness/reins/*`、`DISTRIBUTION.md`、`HOST_COMPATIBILITY.md` 主体必须中文。
- **`scripts/prd_reader.py` 是可选依赖**：任何提到它的地方都必须同时说明"脚本不可执行时降级为纯文本分析"。
- **核心能力固定 7 项**，改动必须同时更新 `skills/testcase-generator/SKILL.md` / `.../prompts/phase*.md` / `.../resources/output_artifacts.md` / `skill.manifest.json` 四处，否则跑 `doc_consistency_audit.py` 会失败。

---

## 边界

- 以下目录**全部已 gitignore**，由 `test-generator activate` 生成：`.claude/` `.codebuddy/` `.agents/` `.cursor/` `.qoder/` `.trae/` `.windsurf/` `.openclaw/` `node_modules/`。不要手工编辑，不要强制提交。
- **`skills/` 不是镜像目录，而是 canonical 技能树，必须被跟踪。** 不要把它加回 `.gitignore`，也不要把它写进 manifest 的 `分发排除` 或 `package_skill.py` 的禁入规则 —— 那样会直接丢掉整个技能。
- `.skill` / `.zip` 是打包产物（包中包），不要提交。
- `test-output/` 是本地验证产物，不要提交。
- **不要删除 `.workbuddy/`** —— 里面是项目记忆与工作日志。
- 不要手工编辑 `skills/testcase-generator/knowledge/index.json`（由 `build_index.py` 生成，且不入包）。

---

## 坑（已经踩过的）

- **openclaw 的入口名 `skill.md` 与技能入口 `SKILL.md` 在大小写不敏感的文件系统上同路。** 标准布局（`SKILL.md` 位于 `skills/testcase-generator/`）已让两者不再同层，因此该冲突**不复存在**；`lib/activation.js` 仍保留基于文件名的冲突保护作为纵深防御，触发时输出 `skipped 'skill.md'` 提示。
- **`npm test` 当前等价于 `node --test "test/**/*.test.js"`。** 直接写 `node --test test` 会把 `test` 当作入口模块并报 `MODULE_NOT_FOUND`。
- **`doc_consistency_audit.py` 的 `version_alignment` 要求 README 第一行 H1 含 `vX.Y.Z`。** 只改 `SKILL.md` 的 frontmatter 会让这项 fail。
- **本仓库以 CRLF 检出。** 在测试中断言文件内容时用 `\r?\n`，否则会在 Windows 上误报失败。
- **`capability_audit.py` 的部分能力标记扫描的是 `skills/testcase-generator/resources/output_artifacts.md`**，不是 `SKILL.md`。把 SKILL.md 的章节下沉到 `references/` 时，请先确认标记仍可被审计发现。
- **技能树内的文件引用技能树外的文件要跨三层。** 例如 `references/x.md` 指向仓库的 `docs/` 需要写 `../../../docs/...`（`references` → `testcase-generator` → `skills` → 仓库根）。

---

## 提交前

按 [`.harness/AGENTS.md`](.harness/AGENTS.md) 第 5 节的 PR 模板与检查清单执行；本仓库使用 Conventional Commits（`feat(scope):` / `fix(scope):` / `docs(scope):` / `chore:`）。
