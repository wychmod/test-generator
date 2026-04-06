# 打包指南

## 快速打包

```bash
# 方式一：直接运行 Python 脚本
python scripts/_do_package.py

# 方式二：Windows 用户双击运行
run_package.bat
```

打包产物：`testcase-generator.zip`（生成在项目根目录）

## 打包脚本说明

`scripts/_do_package.py` 会排除以下文件和目录：

| 类别 | 排除项 |
|------|--------|
| 临时文件 | `_pkg_log.txt`、`_pkg_result.txt`、`package_log.txt`、`PACKAGING.md` |
| 打包脚本 | `scripts/_do_package.py`、`run_package.bat` |
| 输出目录 | `test-output/` |
| Python 环境 | `.venv/`、`.git/`、`.idea/`、`.workbuddy/` |
| 其他 | `__pycache__`、`.DS_Store`、`testcase-generator.zip` |

## 打包后验证

```bash
# 查看 ZIP 内容
python -c "import zipfile; [print(n) for n in sorted(zipfile.ZipFile('testcase-generator.zip').namelist())]"
```

## 手动新增打包文件

如需将新文件/目录纳入打包，确保它不在 EXCLUDE 列表中即可。

---

## 用户安装指南

### 方式一：Vercel skills CLI（推荐）

安装 Vercel 官方的 skills 工具后，可直接从 GitHub 安装：

```bash
# 安装 skills CLI
npm install -g skills

# 从 GitHub 安装（需先将项目推送到 GitHub）
npx skills add <owner>/testcase-generator -y

# 或安装指定分支
npx skills add <owner>/testcase-generator#main -y
```

> **前提**：将项目上传至 GitHub 仓库。

### 方式二：OpenSkills CLI

```bash
# 全局安装
npm install -g openskills

# 从 GitHub 安装
npx openskills install <owner>/testcase-generator
```

### 方式三：手动下载 ZIP

1. 下载 `testcase-generator.zip`
2. 解压到 `~/.claude/skills/testcase-generator/`（Claude Code）或对应工具的 skills 目录

### 方式四：从 ZIP 直接安装（部分工具支持）

```bash
npx skills add ./testcase-generator.zip
```

---

## 发布到 GitHub 前检查清单

- [ ] `SKILL.md` 位于仓库根目录
- [ ] `README.md` 包含安装和使用说明
- [ ] 所有相关文件（prompts/、config/、templates/、resources/）在根目录
- [ ] `.gitignore` 排除了 `.venv/`、`test-output/`、`.idea/` 等
