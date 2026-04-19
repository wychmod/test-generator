# 分发清单

本文档定义 `testcase-generator` 作为可拔插 Skill 分发时的入包边界、排除规则与发布检查项。

## 分发目标

将当前项目整理为一个可安装、可迁移、可复用的测试用例生成 Skill 包。

推荐产物名：

```text
testcase-generator.skill
```

兼容产物名：

```text
testcase-generator.zip
```

> 如果宿主平台支持标准 Skill 包，优先使用 `.skill`；仅在宿主平台只接受 ZIP 时再使用 `.zip`。

## 必须入包

以下文件和目录属于 Skill 运行时资产，必须进入分发包。

| 路径 | 用途 |
|---|---|
| `SKILL.md` | Skill 入口文件，负责触发说明、执行规则与资源路由 |
| `README.md` | 面向使用者和维护者的说明文档 |
| `config/` | 配置 Schema 与示例配置 |
| `prompts/` | 六阶段分析与生成提示词 |
| `resources/` | 质量检查、格式规范、反馈模板与阶段产物协议 |
| `templates/` | 需求、状态图、测试用例等标准输出模板 |
| `scripts/prd_reader.py` | 本地 PRD / Markdown / PDF 文件读取辅助工具 |
| `skill.manifest.json` | 中文分发元数据与入包边界说明 |

## 建议排除

以下内容不应进入最终分发包。

| 路径 | 排除原因 |
|---|---|
| `test-output/` | 本地验证产物，不属于运行时资产 |
| `skills/` | 镜像副本，应该由发布流程生成，不应作为主源打包 |
| `.claude/` | 宿主镜像副本，避免重复和版本漂移 |
| `.agents/` | 宿主镜像副本，避免重复和版本漂移 |
| `.qoder/` | 宿主镜像副本，避免重复和版本漂移 |
| `.trae/` | 宿主镜像副本，避免重复和版本漂移 |
| `.workbuddy/` | 本地工作记忆与环境配置，不能分发 |
| `.git/` | 版本控制目录，不能分发 |
| `.idea/` | IDE 本地配置，不能分发 |
| `.venv/` | 本地 Python 环境，不能分发 |
| `__pycache__/` | Python 缓存，不能分发 |
| `_pkg_log.txt` | 本地打包日志，不能分发 |
| `_pkg_result.txt` | 本地打包结果，不能分发 |
| `package_log.txt` | 本地打包日志，不能分发 |
| `skills-lock.json` | 宿主侧锁定文件，不属于 Skill 运行时资产 |
| `testcase-generator.zip` | 兼容打包产物，避免包中包 |
| `testcase-generator.skill` | 标准打包产物，避免包中包 |

## 开发工具处理

以下文件建议保留在仓库，但不进入运行时分发包。

| 当前路径 | 建议长期位置 | 说明 |
|---|---|---|
| `devtools/package_skill.py` | `devtools/package_skill.py` | 打包工具，不属于 Skill 运行时能力 |
| `devtools/capability_audit.py` | `devtools/capability_audit.py` | 审计工具，不属于普通使用场景 |
| `run_package.bat` | `devtools/run_package.bat` | Windows 打包入口，不属于运行时资产 |
| `PACKAGING.md` | `docs/PACKAGING.md` 或保留根目录 | 发布维护说明，不属于 Skill 执行资产 |

当前阶段已经完成开发工具迁移；后续如需进一步收口，可再将 `run_package.bat` 与发布文档统一收纳到 `devtools/` / `docs/`。

## 推荐分发包内容树

```text
testcase-generator/
├── SKILL.md
├── README.md
├── skill.manifest.json
├── config/
│   ├── example-config.json
│   └── testcase-config-schema.json
├── prompts/
│   ├── phase0_input_preprocessing_prompt.md
│   ├── phase1_requirements_prompt.md
│   ├── phase2_code_analysis_prompt.md
│   ├── phase3_domain_analysis_prompt.md
│   ├── phase4_mbt_design_prompt.md
│   └── phase5_testcase_generation_prompt.md
├── resources/
│   ├── feedback_template.md
│   ├── output_artifacts.md
│   ├── quality_checklist.md
│   └── testcase_formats.md
├── templates/
│   ├── requirements_template.md
│   ├── state_diagram_template.md
│   └── testcase_template.md
└── scripts/
    └── prd_reader.py
```

## 发布前检查项

发布前逐项确认：

- [ ] `SKILL.md` 位于分发包根目录。
- [ ] `SKILL.md` 主体内容为中文。
- [ ] `SKILL.md` 的 description 能覆盖主要触发场景。
- [ ] `resources/output_artifacts.md` 存在，且承接详细阶段产物说明。
- [ ] `config/`、`prompts/`、`resources/`、`templates/` 均已入包。
- [ ] 本地验证产物 `test-output/` 未入包。
- [ ] 多宿主镜像目录未入包。
- [ ] 本地工作记忆 `.workbuddy/` 未入包。
- [ ] 分发包内不存在 `skills-lock.json`、旧 ZIP 或包中包。
- [ ] 同时生成 `.skill` 与 `.zip` 两种产物，且内容一致。
- [ ] 抽样打开包内 Markdown，确认中文内容未乱码。

## 后续建议

后续可以把打包脚本升级为读取 `skill.manifest.json` 的 include / exclude 规则，避免脚本和文档规则分叉。
