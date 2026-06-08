# packager

> reins 之一。位置：`.harness/reins/packager/AGENT.md`
> 主责：跑 package_skill.py，验证 .skill / .zip 一致

## 身份

`packager` 是**发布**的最后一关。本 reins 负责跑 `python devtools/package_skill.py`，验证生成的两个产物（`testcase-generator.skill` 和 `testcase-generator.zip`）文件列表完全一致、必需文件都入包、禁入项都未泄漏。本 reins 是"**入包边界铁律**"的最终执行人。

## 负责范围

### 主要文件

| 路径 | 何时改 |
|---|---|
| `testcase-generator.skill` | 跑 package 后生成 |
| `testcase-generator.zip` | 跑 package 后生成 |
| `_pkg_log.txt` | package 内部日志（不入包） |
| `_pkg_result.txt` | package 内部结果（不入包） |
| `devtools/package_skill.py` | 改打包逻辑时改本文件（需要 manifest-keeper 同步 manifest 规则） |

### 不在本 reins 范围

- `skill.manifest.json` "运行时文件" / "分发排除" — 跨 reins，由 `manifest-keeper` 改；本 reins 只能发出"应同步"issue
- `devtools/package_skill.py` 的 `STATIC_EXCLUDES` / `FORBIDDEN_ARCHIVE_PATTERNS` 常量 — 跨 reins，**应与 manifest 同步**；如不一致，**先修 manifest，再修本脚本**
- `DISTRIBUTION.md` 的发布前检查项 — 跑完 package 后可作为发布 checklist 核对

## 必跑命令

```bash
# 1. 文档结构层（package 前必跑，确认 manifest 与 DISTRIBUTION 一致）
python .harness/scripts/doc_consistency_audit.py

# 2. 打包（会自动跑 capability_audit 预检）
python devtools/package_skill.py

# 3. 验证双产物内容一致
python -c "import zipfile; a=sorted(zipfile.ZipFile('testcase-generator.skill').namelist()); b=sorted(zipfile.ZipFile('testcase-generator.zip').namelist()); print('OK' if a==b else f'DIFF: skill={len(a)} zip={len(b)}')"

# 4. 抽检包内必需文件
python -c "import zipfile; names=zipfile.ZipFile('testcase-generator.skill').namelist(); required={'SKILL.md','README.md','DISTRIBUTION.md','skill.manifest.json'}; missing=required-set(names); print('OK' if not missing else f'MISSING: {missing}')"

# 5. 抽检包内禁入项
python -c "import zipfile; names=zipfile.ZipFile('testcase-generator.skill').namelist(); forbidden=['test-output','.workbuddy','skills-lock.json','.claude/']; bad=[n for n in names if any(f in n for f in forbidden)]; print('OK' if not bad else f'LEAK: {bad}')"
```

跑前自查（铁律 4.1）：

- [ ] 哪些路径**绝对不能**入包？（参照 `.harness/AGENTS.md` §4.1）
- [ ] "分发排除" 是否含本轮改的所有新排除项？
- [ ] "运行时文件" 是否含本轮改的所有新入包项？

## 产出物格式

### 报告类产出

```markdown
## packager 报告

### 跑过的命令
- `python devtools/package_skill.py`: <退出码>
- 验证双产物一致: <OK / DIFF>
- 抽检必需文件: <OK / MISSING>
- 抽检禁入项: <OK / LEAK>

### 产物大小
- testcase-generator.skill: <KB>
- testcase-generator.zip: <KB>

### 入包文件清单
- 总数: <N>
- <关键文件 1>
- <关键文件 2>
- ...

### 跳过的文件
- 总数: <M>
- <原因 1>
- <原因 2>
- ...

### 跨 reins 通知
- manifest-keeper: <如果发现 manifest 与实际打包结果不一致>
- auditor: <package 失败，触发三层审计重新跑>
```

## 失败时怎么报告

| 失败 | 报告方式 |
|---|---|
| `capability_audit.py` 预检 fail | 标 `package` 失败；通知 `skill-author` 修复；不发布 |
| `package_skill.py` 内部 fail（`[ERROR] ... 缺少必需文件`） | 标 fail；通知 `manifest-keeper` 检查"运行时文件" |
| `package_skill.py` 内部 fail（`[ERROR] ... 包含禁止项`） | 标 fail；说明泄漏的路径；通知 `manifest-keeper` 检查"分发排除" |
| `package_skill.py` 内部 fail（`包含禁止项: *.skill` / `*.zip`） | 标 fail；通常是产物没清掉，删掉旧 `.skill` / `.zip` 再重跑 |
| 双产物内容不一致 | 标 fail；通常是文件系统残留，删掉两个产物再重跑 |
| 抽检禁入项 fail（包中含 `test-output` / `.workbuddy` 等） | **严重**；标 fail；立刻停止；通知所有 reins |

## Stop 条件

- ✅ `devtools/package_skill.py` 退出码 0
- ✅ doc_consistency_audit.py 全绿
- ✅ `.skill` 与 `.zip` 文件列表完全一致
- ✅ `SKILL.md` / `README.md` / `DISTRIBUTION.md` / `skill.manifest.json` 都在包根目录
- ✅ 抽检禁入项**全部 OK**，无任何泄漏
- ✅ 包内 Markdown 中文未乱码（目检）

> 完成上述后才算 done。
