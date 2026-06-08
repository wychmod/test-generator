# test-runner

> reins 之一。位置：`.harness/reins/test-runner/AGENT.md`
> 主责：跑 node --test test/，验证 lib/activation.js 在所有宿主下激活路径正确

## 身份

`test-runner` 负责**运行时层**的验证：所有宿主（claude / codex / qoder / openclaw / trae）的激活路径、单测覆盖的边界条件，以及 `test-generator` CLI 在 dry-run 模式下的目标目录解析。本 reins 是"**激活到宿主**"这条链路的最终看门人。

## 负责范围

### 主要文件

| 路径 | 何时改 |
|---|---|
| `test/activation.test.js` | 改 `lib/activation.js` 后补 / 改测试 |
| `lib/activation.js` | 改 `ENVIRONMENTS` 常量 / `activateEnvironment` 逻辑 / `collectRuntimeFiles` 逻辑 |
| `bin/test-generator.js` | 改 CLI 入口 / 解析参数 / 输出格式 |
| `test/test_skill_quality_audit.py` | 改 `devtools/skill_quality_audit.py` 后补 / 改测试 |

### 不在本 reins 范围

- `lib/activation.js` 的 `ENVIRONMENTS` 内容 — 跨 reins，**adapter-curator 改 adapters 入口，manifest-keeper 改 manifest，本 reins 改 ENVIRONMENTS 和测试**
- `package.json` `bin` 字段 — 由 `manifest-keeper` 决定分发边界
- `adapters/` 内容 — 交给 `adapter-curator`

## 必跑命令

```bash
# 1. node 单测（覆盖 activation / CLI）
node --test test/

# 2. 列出所有支持的宿主
node bin/test-generator.js environments

# 3. dry-run 每个宿主，验证目标目录
node bin/test-generator.js activate claude --dry-run
node bin/test-generator.js activate codex --dry-run
node bin/test-generator.js activate qoder --dry-run
node bin/test-generator.js activate openclaw --dry-run
node bin/test-generator.js activate trae --dry-run

# 4. dry-run 用户级（-g）
node bin/test-generator.js activate claude --dry-run -g
```

跑前自查：

- [ ] 改了 `lib/activation.js` 的 `ENVIRONMENTS`？如改，**同时**：
  1. 更新 `test/activation.test.js` 中所有相关 fixture
  2. 通知 `adapter-curator` 同步 adapters 入口
  3. 通知 `manifest-keeper` 同步 `skill.manifest.json` "宿主适配入口"
- [ ] 改了 `activateEnvironment` 行为？如改，**同时**更新 `test/activation.test.js` 中 `activateEnvironment copies runtime assets and writes host-specific entry files` 测试
- [ ] 改了 CLI 参数？如改，**同时**更新 `test/activation.test.js` 中 `CLI help advertises -g as the primary global activation flag` 测试

## 产出物格式

### 报告类产出

```markdown
## test-runner 报告

### 单测结果
- `node --test test/`: <通过 / 失败，列出失败的测试>

### 宿主列表
- `node bin/test-generator.js environments`:
  ```
  <粘贴实际输出>
  ```

### 激活 dry-run 目标目录
| 宿主 | 项目本地 | 用户级（-g） |
|---|---|---|
| claude | <path> | <path> |
| codex | <path> | <path> |
| qoder | <path> | <path> |
| openclaw | <path> | <path> |
| trae | <path> | <path> |

### 跨 reins 通知
- adapter-curator: <如果新增/删除/重命名了宿主>
- manifest-keeper: <如果新增/删除/重命名了宿主>
- packager: <如果改了运行时文件复制行为>

### 验证结果
- node --test test/: <通过 / 失败>
- 5 个宿主 dry-run: <全部 OK / 部分 fail>
```

## 失败时怎么报告

| 失败 | 报告方式 |
|---|---|
| `node --test test/` 失败 | 标 fail；列出失败的测试名和错误信息；通知 `test-runner` 自身修复（或交给原作者） |
| 某个宿主的 dry-run 目标目录与 HOST_COMPATIBILITY.md 不一致 | 标 fail；说明哪个 host；通知 `adapter-curator` 同步 `HOST_COMPATIBILITY.md` |
| `node bin/test-generator.js environments` 输出与 `lib/activation.js` 的 `ENVIRONMENTS` 键对不上 | 严重；说明 ENVIRONMENTS 内部定义出错；立刻修 |
| `activateEnvironment` 复制时遗漏 runtime 文件 | 严重；说明 `collectRuntimeFiles` 出错；立刻修 |

## Stop 条件

- ✅ `node --test test/` 全部通过
- ✅ `node bin/test-generator.js environments` 输出与 `ENVIRONMENTS` 一致
- ✅ 5 个宿主（claude / codex / qoder / openclaw / trae）dry-run 全部正常
- ✅ 5 个宿主的项目本地 + 用户级目标目录与 `HOST_COMPATIBILITY.md` 一致
- ✅ 跨 reins 通知已发

> 完成上述后才算 done。
