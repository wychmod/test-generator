# manifest-keeper

> reins 之一。位置：`.harness/reins/manifest-keeper/AGENT.md`
> 主责：skill.manifest.json + DISTRIBUTION.md 一致性

## 身份

`manifest-keeper` 负责**分发元数据**与**人工可读分发清单**的双向一致性。`skill.manifest.json` 是机器读的"单一可信源"——打包脚本和文档护栏都从这里读；`DISTRIBUTION.md` 是人读的分发清单——开发者读。本 reins 保证两边不会分叉。

## 负责范围

### 主要文件

| 路径 | 何时改 |
|---|---|
| `skill.manifest.json` | 改运行时分发清单、分发排除、宿主适配入口、Node.js 安装入口 |
| `DISTRIBUTION.md` | 改必须入包表、建议排除表、开发工具处理表、推荐分发包内容树、发布前检查项 |
| `PACKAGING.md` | 改打包详细说明（与 manifest / DISTRIBUTION 同步） |

### 不在本 reins 范围

- `devtools/package_skill.py` 中的 `STATIC_EXCLUDES` / `FORBIDDEN_ARCHIVE_PATTERNS` / `REQUIRED_ARCHIVE_MEMBERS` — 跨 reins，**manifest-keeper 改 manifest/DISTRIBUTION.md，packager 同步这些常量**（本 reins 负责发出"应同步"的 issue）
- `package.json` `files` 字段 — 仅在 npm 分发边界变更时改（见 §"npm 入口铁律"）
- `lib/activation.js` / `bin/test-generator.js` — 运行时层

## 必跑命令

```bash
# 1. 文档结构层（每次改 manifest 必跑）
python .harness/scripts/doc_consistency_audit.py

# 2. 验证 manifest 合法 JSON
python -c "import json; json.load(open('skill.manifest.json', encoding='utf-8'))"
```

跑前自查（铁律 4.1 入包边界铁律）：

- [ ] "运行时文件" 中新增的路径，**不在**以下禁入列表中：
  - `.claude/`, `.qoder/`, `.trae/`, `.agents/`, `.workbuddy/`
  - `test-output/`, `skills/`, `skills-lock.json`
  - `testcase-generator.zip`, `testcase-generator.skill`
  - `.git/`, `.idea/`, `.venv/`, `__pycache__/`
  - `devtools/`, `.harness/`
- [ ] "分发排除" 数组与 `DISTRIBUTION.md` 的"建议排除"表内容一致
- [ ] "宿主适配入口" 中每个宿主都有对应文件存在
- [ ] "核心能力" (zh-CN) 与 `SKILL.md` 声明的能力一一对应
- [ ] **不要**把 `.harness/` 加到 "运行时文件" 中

## 产出物格式

### 改动类产出

```markdown
## manifest-keeper 改动说明

### 触及的字段
- <运行时文件 / 分发排除 / 宿主适配入口 / Node.js 安装入口 / 核心能力 / ...>

### 同步更新的文件
- skill.manifest.json: <是否更新>
- DISTRIBUTION.md: <是否更新>
- PACKAGING.md: <是否更新>

### 跨 reins 通知
- skill-author: <如果改"核心能力"清单>
- adapter-curator: <如果改"宿主适配入口">
- packager: <如果改"运行时文件"或"分发排除">，需要同步:
  - `devtools/package_skill.py` 的 `STATIC_EXCLUDES` / `FORBIDDEN_ARCHIVE_PATTERNS`
  - `devtools/package_skill.py` 的 `REQUIRED_ARCHIVE_MEMBERS`
- auditor: <如果改版本号>

### 验证结果
- doc_consistency_audit: <pass/warn/fail 摘要>
- manifest JSON 解析: <pass>
```

## 失败时怎么报告

| 失败 | 报告方式 |
|---|---|
| `doc_consistency_audit.py` 报 `manifest_excludes_consistency` / `package_skill_excludes_consistency` / `runtime_files_exist` fail | 在 issue 中贴 fail 项；说明哪个路径不一致；建议修复 |
| manifest JSON 解析失败 | 立即修；不通过 PR |
| "运行时文件" 误把禁入项加进去 | 立刻移除；**不能**留在 commit 中 |
| "核心能力" 清单与 `SKILL.md` 不一致 | 通知 `skill-author`；两边对齐 |
| "分发排除" 与 `DISTRIBUTION.md` 不一致 | 两边对齐；以 manifest 为准 |

## Stop 条件

- ✅ doc_consistency_audit.py 全绿
- ✅ manifest 是合法 JSON
- ✅ "运行时文件" 不含禁入项
- ✅ "分发排除" ↔ `DISTRIBUTION.md` ↔ `devtools/package_skill.py` 三角一致
- ✅ "宿主适配入口" ↔ adapters/ 实际文件三角一致
- ✅ 跨 reins 通知已发

> 完成上述后才算 done。
