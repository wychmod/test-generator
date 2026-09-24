# Operations — 运维与发布

> 打包、发布、宿主激活、CI 等流程文档。

## 现有文档

- [`packaging.md`](packaging.md) — 本地打包 `.skill` / `.zip` 产物，发布前检查清单

## 待写内容

- [ ] **distribution.md**：与根目录 `DISTRIBUTION.md` 互为补充，侧重运维视角
- [ ] **host-compatibility.md**：与根目录 `HOST_COMPATIBILITY.md` 互为补充，侧重激活命令在不同平台的差异
- [ ] **release-checklist.md**：发版流程（版本号更新 → manifest → 评测 → 打包 → npm publish → GitHub release）
- [ ] **ci.md**：本地如何复现 CI 的四层审计（capability / quality / doc_consistency）与 `.harness/eval/run_eval.py` 流水线

## 与根目录 4 份文档的关系

| 根目录 | 这里 | 关系 |
|---|---|---|
| `DISTRIBUTION.md` | （future `distribution.md`） | 根目录版是**入包契约**；这里放**运维实操** |
| `HOST_COMPATIBILITY.md` | （future `host-compatibility.md`） | 根目录版是**适配策略**；这里放**激活命令故障排查** |
| `PACKAGING.md` | `packaging.md` | **已搬入**，根目录不再保留 |

## 工具

- [`../../devtools/package_skill.py`](../../devtools/package_skill.py) — 打包脚本（必需 `README.md` / `DISTRIBUTION.md` / `HOST_COMPATIBILITY.md` / `skill.manifest.json`，以及技能入口 `skills/testcase-generator/SKILL.md`）
- [`../../bin/test-generator.js`](../../bin/test-generator.js) — Node.js CLI 入口
- [`../../lib/activation.js`](../../lib/activation.js) — 宿主激活逻辑
