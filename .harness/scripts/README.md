# 文档护栏脚本

> 位置：`.harness/scripts/`
> 主责：跑文档结构层的一致性检查

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `doc_consistency_audit.py` | 6 类文档一致性检查（版本号 / 能力矩阵 / 宿主表 / npm 入口 / 运行时清单 / 排他规则） |

## doc_consistency_audit.py

### 执行 6 类检查

| # | 检查项 | 失败影响 | 谁来修 |
|---|---|---|---|
| 1 | **版本号三处一致**（SKILL.md front matter / README.md 标题 / skill.manifest.json "版本"） | 必须修，否则 `fail` | skill-author + manifest-keeper |
| 2 | **能力矩阵覆盖**（manifest.核心能力 ↔ SKILL.md ↔ prompts/phase*.md ↔ resources/output_artifacts.md） | `fail`：核心能力未在 SKILL.md 出现 | skill-author |
| 3 | **宿主表三方一致**（HOST_COMPATIBILITY.md ↔ adapters/ 实际目录 ↔ lib/activation.js 的 ENVIRONMENTS） | `fail`：缺入口或缺注册 | adapter-curator + test-runner |
| 4 | **npm 脚本入口**（test-generator 在 README / package.json / HOST_COMPATIBILITY 都有提到） | `fail`：三处缺一不可 | manifest-keeper |
| 5 | **运行时分发清单**（manifest.运行时文件 实际都存在） | `fail`：清单中的文件/目录不存在 | manifest-keeper |
| 6 | **排他规则一致性**（DISTRIBUTION.md 建议排除/开发工具 ↔ manifest.分发排除 ↔ devtools/package_skill.py 的 STATIC_EXCLUDES + FORBIDDEN_ARCHIVE_PATTERNS） | `fail`：关键禁入项未声明 | manifest-keeper + packager |

### 用法

```bash
# 默认输出 markdown 报告
python .harness/scripts/doc_consistency_audit.py

# 输出 JSON（便于 CI 集成）
python .harness/scripts/doc_consistency_audit.py --format json

# 查看帮助
python .harness/scripts/doc_consistency_audit.py --help
```

### 退出码

- `0`：没有 fail（可以有 warn）
- `1`：至少一个 fail

### 在 PR 流程中

每次 PR 之前**必须**跑本脚本，全绿才能合并：

```bash
# 完整三层审计
python devtools/capability_audit.py
python devtools/skill_quality_audit.py
python .harness/scripts/doc_consistency_audit.py
```

### 输出示例

```text
# 文档一致性审计报告 (doc_consistency_audit)

- 仓库根目录：`D:\pycharm\test-generator`
- 报告时间：由 doc_consistency_audit.py 实时生成

| Check | Status | Detail |
| --- | --- | --- |
| version_alignment | pass | 三处版本号一致：2.1.0 |
| ... | ... | ... |

- Passed: 12
- Warned: 0
- Failed: 0
```

### 不修改任何文件

本脚本**只读**，不修改任何项目文件。修复时按 fail / warn 列表交给对应 reins。

### 适用范围

- 当前仓库根：`D:\pycharm\test-generator`
- 自动以脚本所在位置向上两级定位仓库根
- 不接受 `--root` 参数（避免误用）

## 与其他护栏脚本的关系

```
devtools/capability_audit.py      →  能力声明层（必需文件、版本对齐、Schema）
devtools/skill_quality_audit.py   →  内容质量层（必填字段、阶段流水线、标准引用）
.harness/scripts/
  doc_consistency_audit.py        →  文档结构层（本次新增）
```

三层全绿 → 改动可合并。
