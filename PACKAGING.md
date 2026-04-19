# 打包指南

## 快速打包

```bash
# 方式一：直接运行 Python 脚本
python devtools/package_skill.py

# 方式二：Windows 用户双击运行
run_package.bat
```

当前会同时生成两个分发产物：

- 推荐标准分发产物：`testcase-generator.skill`
- 兼容分发产物：`testcase-generator.zip`

> 如果宿主平台支持标准 Skill 包，优先使用 `.skill`；仅在宿主平台只接受 ZIP 时再使用 `.zip`。

## 分发边界

分发包的入包与排除规则以以下文件为准：

- `skill.manifest.json`：机器可读的中文分发元数据与文件边界，是打包脚本的单一来源。
- `DISTRIBUTION.md`：人工可读的分发清单、排除原因和发布检查项。

## 打包脚本说明

`devtools/package_skill.py` 会先执行预检审计，再根据 `skill.manifest.json` 中的运行时文件与分发排除规则统一构建 `.skill` 与 `.zip` 两个产物，并执行归档后自动校验：

| 校验类别 | 说明 |
|------|--------|
| 必需文件 | `SKILL.md`、`README.md`、`DISTRIBUTION.md`、`skill.manifest.json` 必须入包 |
| 禁止项 | `test-output/`、`.workbuddy/`、多宿主镜像、`skills-lock.json`、包中包不得入包 |
| 双产物一致性 | `.skill` 与 `.zip` 文件列表必须完全一致 |

## 打包后验证

```bash
# 查看 .skill 内容
python -c "import zipfile; [print(n) for n in sorted(zipfile.ZipFile('testcase-generator.skill').namelist())]"

# 查看 .zip 内容
python -c "import zipfile; [print(n) for n in sorted(zipfile.ZipFile('testcase-generator.zip').namelist())]"
```

重点确认：

- `SKILL.md` 在包根目录。
- `skill.manifest.json` 已入包。
- `DISTRIBUTION.md` 已入包。
- `config/`、`prompts/`、`resources/`、`templates/` 已入包。
- `test-output/` 未入包。
- `.workbuddy/` 未入包。
- 多宿主镜像目录未入包。
- `skills-lock.json` 未入包。
- `.skill` 和 `.zip` 两个产物内容一致。
- 包内 Markdown 中文未乱码。

## 手动新增打包文件

如需将新文件或目录纳入打包，需要同时确认：

1. 已记录到 `skill.manifest.json` 的“运行时文件”或“分发排除”中。
2. 已在 `DISTRIBUTION.md` 中说明用途。
3. 如有必要，补充 `devtools/capability_audit.py` 的审计规则。
4. 已重新执行打包并验证两个产物内容一致。

---

## 用户安装指南

### 方式一：Vercel skills CLI

安装 Vercel 官方的 skills 工具后，可从 GitHub 安装：

```bash
# 安装 skills CLI
npm install -g skills

# 从 GitHub 安装（需先将项目推送到 GitHub）
npx skills add <owner>/testcase-generator -y

# 或安装指定分支
npx skills add <owner>/testcase-generator#main -y
```

> 前提：将项目上传至 GitHub 仓库。

### 方式二：OpenSkills CLI

```bash
# 全局安装
npm install -g openskills

# 从 GitHub 安装
npx openskills install <owner>/testcase-generator
```

### 方式三：手动下载标准 Skill 包

1. 下载 `testcase-generator.skill`。
2. 将其导入支持 `.skill` 的宿主工具，或重命名为 `.zip` 后在仅支持 ZIP 的环境中解压使用。

### 方式四：手动下载 ZIP

1. 下载 `testcase-generator.zip`。
2. 解压到目标宿主的 skills 目录，例如 `~/.claude/skills/testcase-generator/` 或对应工具的 Skill 目录。

### 方式五：从本地包直接安装

部分工具支持：

```bash
npx skills add ./testcase-generator.skill
# 或
npx skills add ./testcase-generator.zip
```

---

## 发布到 GitHub 前检查清单

- [ ] `SKILL.md` 位于仓库根目录。
- [ ] `SKILL.md` 主体为中文内容。
- [ ] `README.md` 包含安装和使用说明。
- [ ] `skill.manifest.json` 已更新。
- [ ] `DISTRIBUTION.md` 已更新。
- [ ] 所有相关文件 `prompts/`、`config/`、`templates/`、`resources/` 在根目录。
- [ ] `.gitignore` 排除了 `.venv/`、`test-output/`、`.idea/` 等本地目录。
- [ ] 多宿主镜像目录不作为主源维护。
- [ ] 根目录中的 `.skill` / `.zip` 产物不作为源码提交。



