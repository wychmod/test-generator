# 新增 AI 宿主适配器

> 目的：在不破坏 canonical source + host adapter 架构的前提下，把 testcase-generator 接入新的 AI 工具 / IDE。
>
> 现有 8 个适配器：`claude` / `codebuddy` / `codex` / `cursor` / `openclaw` / `qoder` / `trae` / `windsurf`
>
> 相关：[`../../HOST_COMPATIBILITY.md`](../../HOST_COMPATIBILITY.md)（完整兼容策略）/ [`contributing.md`](contributing.md)（PR 流程）/ [`../../.harness/reins/adapter-curator/AGENT.md`](../../.harness/reins/adapter-curator/AGENT.md)（适配器策展 agent 角色）

---

## 1. 决策树：完整适配 vs 软适配

不是所有宿主都需要完整的适配入口。先判断：

```
该宿主是否有 SKILL.md / AGENTS.md / 类似的多文件入口规范？
    │
    ├── 是 → 完整适配（参考 claude / codebuddy / qoder / trae）
    │        入口：adapters/<host>/SKILL.md（或对应文件名）
    │        激活后从仓库根读取所有运行时文件
    │
    └── 否（只有单文件 rules / settings 风格入口）→ 软适配（参考 cursor / windsurf）
            入口：adapters/<host>/<host>rules.md
            激活时复制为根目录单文件（如 .cursorrules / .windsurfrules）
            容量小，必须显式说明 fallback 策略
```

**判断点**：
- 是否能稳定从指定目录加载多个 Markdown 文件
- 是否能在系统提示词或规则集中引用多个文件路径
- 是否支持 SKILL.md 风格的 YAML frontmatter `description` 触发

如果答案是"全部是"，做完整适配；任何一个"否"，做软适配。

---

## 2. 完整适配的 8 步流程

### Step 1：建目录

```bash
mkdir -p adapters/<host>/
```

`<host>` 必须是小写字母 + 数字 + 连字符（与 `lib/activation.js` 中 `ENVIRONMENTS` 的 key 一致）。

### Step 2：写入口文件

入口文件名按宿主约定：

| 约定 | 入口文件 |
|---|---|
| Claude 风格（`SKILL.md`） | `adapters/<host>/SKILL.md` |
| Codex / OpenAI Agents（`AGENTS.md`） | `adapters/<host>/AGENTS.md` |
| OpenClaw（`skill.md` 小写） | `adapters/<host>/skill.md` |
| Cursor 软适配（`cursorrules.md`） | `adapters/cursor/cursorrules.md` |
| Windsurf 软适配（`windsurfrules.md`） | `adapters/windsurf/windsurfrules.md` |

入口文件结构（参考 `adapters/claude/SKILL.md`）：

```markdown
---
name: testcase-generator-<host>-adapter
description: 适配 <host> 类宿主的入口文件。Use when the host expects <约定入口文件名> and <是否支持多文件导航>. Trigger for requests about generating, reviewing, expanding, or standardizing test cases, test scenarios, or MBT-oriented testing outputs.
---

# <Host> Adapter for Testcase Generator

这是 `testcase-generator` 的 <host> 类宿主适配入口。

## 适用场景
当用户提出以下需求时触发：
- 生成测试用例
- 评审或补全测试场景
- MBT 导向测试设计
- 结构化测试设计文档

## 使用方式
1. 优先理解技能树入口 `skills/testcase-generator/SKILL.md` 的核心规则。
2. 根据任务类型继续读取：
   - `skills/testcase-generator/prompts/` 中的阶段提示词
   - `skills/testcase-generator/resources/` 中的质量与格式规范
   - `skills/testcase-generator/templates/` 中的输出模板
3. 若输入为本地文件，可在宿主支持脚本时使用 `skills/testcase-generator/scripts/prd_reader.py`。

## 推荐路由
- 完整复杂任务：`skills/testcase-generator/SKILL.md` + `skills/testcase-generator/prompts/` + `skills/testcase-generator/resources/quality_checklist.md`
- 轻量任务：`skills/testcase-generator/SKILL.md` + `skills/testcase-generator/templates/testcase_template.md`
- 输入质量较差：先参考 `skills/testcase-generator/resources/output_artifacts.md` 的阻断与假设规则

## Fallback
如果宿主不能稳定执行脚本：
- 直接基于用户提供的文本内容执行
- 不依赖 `skills/testcase-generator/scripts/prd_reader.py`
- 明确标记基于文本推断的假设项
```

**关键约束**：
- **不要复制核心 prompts / templates / resources**。适配层是路由层，不是复制层。
- 顶部 YAML `description` 必须包含 host 名 + 触发场景，让宿主能可靠识别。
- 中文为主。

### Step 3：注册到 `lib/activation.js`

在 `ENVIRONMENTS` 字典中添加条目：

```js
const ENVIRONMENTS = {
  // ... 现有 8 个 ...
  <host>: {
    localPath: [".<host>", "skills", "testcase-generator"],  // 项目级目录约定
    globalPath: ["~", ".<host>", "skills", "testcase-generator"],  // 用户级目录约定
    // 仅当入口文件名不是 SKILL.md 时加 entry 字段
    entry: {
      source: path.join("adapters", "<host>", "<ENTRY_FILENAME>"),
      target: "<DEST_FILENAME>",  // 激活时复制到目标目录的文件名
    },
  },
};
```

判断要点：
- `localPath`：项目内激活目录（相对项目根）
- `globalPath`：用户级激活目录（`-g` 激活）
- `entry`：仅当宿主约定的入口文件名不是 `SKILL.md` 时需要

### Step 4：同步 `package.json` 的 `files`

`files` 字段当前是 `["SKILL.md", "README.md", "DISTRIBUTION.md", "HOST_COMPATIBILITY.md", "adapters", ...]`。

`adapters/` 已经被整目录打包，**无需修改**。但如果你新增 `bin/` 或 `lib/` 之外的目录，需要追加。

### Step 5：同步 `skill.manifest.json`

在 `宿主适配入口` 字段中添加：

```json
{
  "宿主适配入口": {
    "claude": "adapters/claude/SKILL.md",
    // ... 现有 8 个 ...
    "<host>": "adapters/<host>/<ENTRY_FILENAME>"
  }
}
```

同时更新：

- `适用场景.zh-CN` 和 `适用场景.en-US` 中提到新宿主时
- `Node.js安装入口.支持环境` 数组中追加 `"<host>"`

### Step 6：同步 `HOST_COMPATIBILITY.md`

在「宿主适配入口」表中追加一行：

```markdown
| <Host 名> | `adapters/<host>/<ENTRY_FILENAME>` | <语言策略> | <推荐程度：高/中> |
```

并在「Node.js 激活入口」表中追加：

```markdown
| `<host>` | `.<host>/skills/testcase-generator` | <额外入口约定> |
```

如果该宿主有特殊的 fallback / 能力降级，在「能力差异与降级策略」章节补充。

### Step 7：审计 + 测试

```bash
# 1. 能力审计（必须全绿）
python devtools/capability_audit.py

# 2. Node 测试（含新环境；用 npm test，勿写成 glob）
npm test

# 3. Python 测试
npm run test:python

# 4. 文档护栏（宿主表三方一致）
python .harness/scripts/doc_consistency_audit.py

# 5. 打包验证（必须生成两个产物）
python devtools/package_skill.py

# 6. dry-run 验证激活逻辑
node bin/test-generator.js activate <host> --dry-run
```

### Step 8：本地激活实测

```bash
# 在临时目录测试激活
mkdir /tmp/test-host-activate && cd /tmp/test-host-activate
node /path/to/test-generator/bin/test-generator.js activate <host> --dry-run
node /path/to/test-generator/bin/test-generator.js activate <host>

# 检查激活结果
ls -la .<host>/skills/testcase-generator/
# 或对软适配：
cat .<entry_filename>
```

**验证清单**：
- [ ] 入口文件被复制到目标目录
- [ ] 运行时文件（`skills/testcase-generator/` 下的 prompts/、resources/、templates/）齐全
- [ ] 如果有 `entry`，目标文件名与约定一致
- [ ] 全局激活（`-g`）路径正确

---

## 3. 软适配的特殊处理

软适配（参考 `adapters/cursor/cursorrules.md`）有三个额外约束：

### 3.1 单文件容量约束

`.cursorrules` / `.windsurfrules` 等单文件规则容量通常 < 几 KB。**不能直接复制完整的 SKILL.md**，必须做摘要：

- 仅保留触发场景 + 推荐阅读顺序 + 工作原则
- 详细方法论通过"推荐阅读根目录 SKILL.md"链接出去
- Fallback 策略必须显式列出（上下文紧张时怎么办）

### 3.2 必须显式声明 "soft adapter"

入口文件第一段必须声明是软适配，解释：

- 宿主为什么不消费 SKILL.md（单文件规则限制）
- 当前入口文件会被复制为什么名字（如 `.cursorrules`）
- 这是路由提示而非方法论替代品

参考：`adapters/cursor/cursorrules.md` 第 1-5 行。

### 3.3 强制 fallback

软适配必须包含完整的 fallback 章节，因为上下文预算紧张时宿主可能只读这一个文件：

```markdown
## Fallback (when context is tight)
- 仅输出测试点清单（不生成完整用例）
- 优先覆盖边界条件 + 异常路径
- 显式标记 [推断] 假设
- 引导用户跑完整流程时回到根目录 SKILL.md
```

---

## 4. 适配器变更的同步点汇总

新增或修改一个适配器，**必须**在以下 8 处同步：

| # | 文件 | 同步内容 |
|---|---|---|
| 1 | `adapters/<host>/<entry>` | 新增或修改入口文件 |
| 2 | `lib/activation.js` | `ENVIRONMENTS` 字典 + （必要时）`ENV_ALIASES` |
| 3 | `skill.manifest.json` | `宿主适配入口` + `适用场景` + `Node.js安装入口.支持环境` |
| 4 | `HOST_COMPATIBILITY.md` | 入口表 + 激活表 + （必要时）降级策略章节 |
| 5 | `package.json` | `files`（通常无需改动，`adapters/` 已涵盖） |
| 6 | `README.md` | 触发命令示例中提到新环境名 |
| 7 | `skills/testcase-generator/SKILL.md` 顶部 YAML | `description` 中括号备注新环境（如有空间） |
| 8 | `dist/manifest 测试` | `npm test` 自动覆盖 |

漏掉任何一处都会导致：

- 漏 `HOST_COMPATIBILITY.md` → 用户找不到适配说明
- 漏 `skill.manifest.json` → 打包审计漏检、运行时跳过该环境
- 漏 `lib/activation.js` → `test-generator activate <host>` 直接抛 `Unsupported environment`
- 漏 `package.json` → npm 包分发缺文件

---

## 5. 适配器健康度自检

每次适配器变更后，跑这个 4 步检查：

```bash
# 1. 入口文件存在性
python devtools/capability_audit.py | grep "<host>"

# 2. activation.js 注册
node -e "console.log(Object.keys(require('./lib/activation').ENVIRONMENTS).join(','))"

# 3. manifest 注册
node -e "console.log(JSON.stringify(require('./skill.manifest.json')['宿主适配入口'], null, 2))"

# 4. 实际激活
node bin/test-generator.js activate <host> --dry-run
```

四项输出都应该包含 `<host>`。任何一项缺失，停下来修复。

---

## 6. 适配器命名约定

| 命名 | 适用 |
|---|---|
| `<host>` 全小写 | `ENVIRONMENTS` key、`adapters/` 目录、`activate` 命令参数 |
| `Adapters/<Host>` 首字母大写 | `HOST_COMPATIBILITY.md` 表格中的人类可读名 |
| `<host>.skill` / `<host>rules.md` | 文件名（除非宿主有特定约定） |
| `--target <path>` | 单环境激活时的可选路径 |

**不要**：
- ❌ 使用中文 / emoji / 空格作为环境名
- ❌ 使用 `_`（用 `-`）
- ❌ 大小写混用（host 名必须小写）
- ❌ 与现有 8 个冲突（claude / codebuddy / codex / cursor / openclaw / qoder / trae / windsurf）

---

## 7. 常见失败模式与排错

| 症状 | 原因 | 修复 |
|---|---|---|
| `Unsupported environment 'xxx'` | 没在 `lib/activation.js` 注册 | 加 `ENVIRONMENTS.xxx` |
| 审计报告找不到 host 入口 | 没在 `skill.manifest.json` 加 | 加 `宿主适配入口.xxx` |
| `activate xxx --dry-run` 没列出新环境 | `supportedEnvironments()` 返回的还是旧字典 | 检查 `ENVIRONMENTS` 是否正确导出 |
| npm 包里没有新 adapter 文件 | `package.json` 的 `files` 漏写 | 一般不需要（`adapters/` 已涵盖），但若新增目录需补 |
| `.cursorrules` 找不到 | `entry.target` 拼错 | 检查 `entry.target` 与宿主约定一致 |
| 测试 fixture 创建失败 | `test/activation.test.js` 的 `makeFixtureRoot()` 没列新文件 | 临时补测试（通常不需要，因为测试是按动态 manifest 跑的） |
