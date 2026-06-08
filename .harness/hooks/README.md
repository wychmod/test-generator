# .harness/hooks/ — Git 钩子与打包前护栏

本目录提供 `testcase-generator` 仓库的提交前 / 打包前护栏脚本，以及把脚本
安装为 git 钩子的安装器。所有脚本都是**纯 Python**（无 shell 依赖），
可在 Windows、Linux、macOS 上直接运行。

## 文件清单

| 文件 | 角色 | 平台 |
|---|---|---|
| `precommit.py` | 提交前按需审计 | Windows / Linux / macOS |
| `prepackage.py` | 打包前跑完整审计 | Windows / Linux / macOS |
| `install-hooks.ps1` | Windows 钩子安装器 | Windows |
| `install-hooks.sh` | POSIX 钩子安装器 | Linux / macOS |

## 触发规则（precommit.py）

`precommit.py` 读取 `git diff --cached --name-only`，按暂存文件分桶触发
不同的审计。`--all` 忽略 diff 跑全部，`--dry-run` 只报告不 fail。

| 暂存文件落在 | 触发的审计 | 理由 |
|---|---|---|
| `SKILL.md` / `skill.manifest.json` / `package.json` | `capability_audit.py` | 改了能力声明 / 入口 / 分发元数据 |
| `prompts/` / `templates/` / `resources/` | `skill_quality_audit.py` | 改了提示词 / 模板 / 质量门禁 token |
| `lib/` / `bin/` | `node --test test/` | 改了 npm CLI 或激活逻辑 |
| `adapters/` | `node bin/test-generator.js activate <env> --dry-run` | 改任何宿主入口都验证所有宿主仍能激活 |
| `DISTRIBUTION.md` / `skill.manifest.json` | 提醒人工同步 `分发排除` ↔ `必入包` 列表 | 文档双写一致性 |
| `.harness/` | 提醒人工 review（不阻断） | 治理文件改动需人工确认 |

> 提示：触发是**或**关系——一次提交里同时改了 SKILL.md 和 prompts，会
> 同时跑 `capability_audit.py` + `skill_quality_audit.py`。

## 预打包审计（prepackage.py）

按 `.harness/AGENTS.md` 「必跑命令」的顺序，串行跑以下四步，**全部
通过**才返回 0：

1. `python devtools/capability_audit.py`
2. `python devtools/skill_quality_audit.py`
3. `python .harness/scripts/doc_consistency_audit.py`
4. `node --test test/`

任一 `fail` 或 `error` 都会让脚本返回 1。`--dry-run` 只报告不 fail；
`--json` 输出结构化报告。

## 安装

从仓库根目录执行：

```bash
# Linux / macOS
bash .harness/hooks/install-hooks.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .harness/hooks/install-hooks.ps1
```

安装器会：

1. 检查 `.git/` 目录存在。
2. 复制 `precommit.py` / `prepackage.py` 到 `.git/hooks/pre-commit` /
   `.git/hooks/pre-package`。
3. POSIX 上 `chmod +x` 给执行权限。
4. 如果目标钩子已存在但**不属于本仓库**（即不含 `testcase-generator`
   标识），**拒绝覆盖**并报错——这样不会破坏其他项目的钩子。

> Git 自身会把任何 `pre-commit` 可执行文件当成钩子。复制过去的 Python
> 脚本默认没 `+x`，所以 Windows 用户在安装时 PowerShell 不会主动加
> `+x`；如果你的 `core.hooksPath` 设置成 `.git/hooks`，确保 git
> 客户端能执行 `.py` 即可（git for Windows 自带的 Python 启动器会按
> shebang 调用 `python`）。

## 手动调用

```bash
# 看 precommit 会跑什么
python .harness/hooks/precommit.py --dry-run

# 真实跑一次（任何 fail → 退出码 1）
python .harness/hooks/precommit.py

# 不按 diff 跑所有
python .harness/hooks/precommit.py --all

# 预打包
python .harness/hooks/prepackage.py --dry-run
python .harness/hooks/prepackage.py --json > pre-package-report.json
```

## 跨平台说明

- 全部使用 `subprocess.run([...], shell=False)`，避免 Windows / POSIX
  shell 解析差异。
- 路径用 `pathlib.Path`，自动适配 `\` 与 `/`。
- 颜色 / 终端控制全部省略，输出是纯文本，方便 CI 抓取。
- 没有 `requests` / `urllib` / `httpx` 等网络依赖——所有审计都是
  本地静态检查。

## 与 `.harness/AGENTS.md` 的关系

本目录的脚本是 `.harness/AGENTS.md` §3「必跑命令」的具体落地：

- 提交前按需跑 §3 里的 capability / skill_quality / node --test
- 打包前按顺序跑 §3 里的全部四条

任何对「必跑命令」的修改必须**同时**更新 `precommit.py` 的触发桶和
`prepackage.py` 的 `DEFAULT_AUDITS` 顺序。
