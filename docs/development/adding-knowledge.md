# 如何添加知识库条目

> 本指南面向**普通用户**（添加自己的项目知识）和**贡献者**（改进示例源）。
>
> 架构说明：[`../architecture/knowledge-base.md`](../architecture/knowledge-base.md)
>
> sources 使用说明：[`../../knowledge/sources/README.md`](../../knowledge/sources/README.md)

---

## 1. 普通用户：3 步添加知识

### Step 1：写一个 `.md` 文件

```bash
# 示例：添加项目支付术语表
$EDITOR knowledge/sources/payment-glossary.md
```

最小可用文件：

```markdown
# 支付术语表

## 支付宝回调
异步通知，商户需返回 "success" 字符串才算接收成功。

## 微信支付 V3
使用 APIv3 签名，需要商户证书。回调需解密。

## 退款时效
已签收后 7 天内可申请退款。
```

### Step 2（可选）：添加 frontmatter 元数据

```markdown
---
title: 支付术语表
tags: [payment, glossary]
priority: high
updated: 2026-06-13
---

# 支付术语表
...
```

| 字段 | 必需 | 说明 |
|---|---|---|
| `title` | 否 | 未指定则用文件名（去掉 `.md`） |
| `tags` | 否 | 数组或逗号分隔，影响检索权重（未来） |
| `priority` | 否 | `high`/`normal`/`low`，影响检索分数（high ×1.5，low ×0.7） |
| `updated` | 否 | ISO 日期，纯展示用 |

### Step 3：重建索引

```bash
python knowledge/scripts/build_index.py
```

输出类似：

```
[ok] index built -> D:\pycharm\test-generator\knowledge\index.json
  sources:    4
  sections:   19
  vocab:      312 terms
```

### Step 4：验证检索

```bash
python knowledge/scripts/search.py "支付宝回调"
```

应该能在结果中看到你刚添加的源。

---

## 2. 文件命名与组织

### 命名约定

| ✅ 推荐 | ❌ 不推荐 |
|---|---|
| `user-auth-glossary.md` | `Untitled.md` |
| `payment-flow.md` | `payment flow.md`（含空格） |
| `compliance-pci-dss.md` | `payment.md`（太泛） |

**原则**：

- 一个文件 = 一个主题（避免"综合知识.md"这种大杂烩）
- 主题用名词短语，不用动词
- 英文小写 + 连字符（与 `lib/activation.js` 命名风格一致）

### 组织策略

```
sources/
├── domain-glossary.md           # 通用术语
├── payment-glossary.md          # 领域术语（按领域拆）
├── auth-glossary.md
├── project-conventions.md       # 项目规范
├── historical-cases-auth.md     # 历史用例（按模块拆）
├── historical-cases-payment.md
├── compliance-rules.md          # 合规条款
└── api-quick-ref.md             # API 速查
```

**粒度建议**：

- 每个文件 50-500 行（太小则分片多，索引过大；太大则检索粗）
- 任何文件超过 1MB 应拆分

---

## 3. 检索测试

添加知识后，跑这套基础测试：

```bash
# 1. 索引构建
python knowledge/scripts/build_index.py --stats

# 2. 直接命中测试
python knowledge/scripts/search.py "你的关键词"

# 3. 触发词检测
python knowledge/scripts/search.py "你的查询" --trigger
```

**如果检索失败**：

| 症状 | 原因 | 修复 |
|---|---|---|
| 完全找不到 | 文件没被读取 | 检查文件名以 `.md` 结尾且**非 `README.md`** |
| 找到但分数低 | 关键词不突出 | 在文档中重复使用目标关键词 2-3 次 |
| 找到错误段落 | 命中了无关内容 | 用更具体的术语 |
| snippet 太短 | 命中词靠后 | 重新组织文档结构，让关键词出现在前 80 字内 |

---

## 4. 贡献者：改进示例源

示例源（`domain-glossary.md`、`project-conventions.md`、`historical-cases.md`）随 v1 进入分发包。改进时注意：

### 4.1 替换 vs 扩展

- **替换**：示例内容明显错误或误导 → 改
- **扩展**：增加更多行业通用示例 → 加新文件（如 `compliance-hipaa.md`）
- ❌ 不要删除示例源 —— 用户可能依赖它们作为参考模板

### 4.2 内容质量标准

| 维度 | 标准 |
|---|---|
| 中立性 | 不带特定公司的内部术语（除非是公开标准） |
| 可验证 | 每个事实可被读者独立查证 |
| 时效性 | 标注 `updated` 字段 |
| 完整性 | 每个主题至少 3 个示例条目 |

### 4.3 同步 manifest

如果新增示例源（不是替换）：

1. 检查 `skill.manifest.json` 中 `运行时文件` 是否包含 `knowledge/sources/**`（已包含则无需改）
2. PR description 中列出新增文件
3. 不需要改 `.gitignore`（`knowledge/index.json` 已忽略）

---

## 5. 常见任务清单

### 任务：批量导入历史用例

```bash
# 1. 把历史用例文件放到 sources
cp old-cases/*.md knowledge/sources/historical-cases-legacy.md

# 2. 编辑 frontmatter
$EDITOR knowledge/sources/historical-cases-legacy.md
# 加：
# ---
# title: 历史用例集（2024 迁移）
# tags: [historical, legacy]
# priority: normal
# ---

# 3. 重建 + 验证
python knowledge/scripts/build_index.py
python knowledge/scripts/search.py "登录" --source historical-cases-legacy
```

### 任务：清理过期知识

```bash
# 1. 直接删除文件
mavis-trash knowledge/sources/old-glossary.md

# 2. 重建索引
python knowledge/scripts/build_index.py --rebuild
```

### 任务：临时禁用某源（不删除）

把文件名加上 `_disabled` 后缀：

```bash
mv knowledge/sources/api-quick-ref.md knowledge/sources/_disabled_api-quick-ref.md
python knowledge/scripts/build_index.py --rebuild
```

**为什么用 `_disabled_` 前缀而不是 .gitignore？** 因为 build_index 扫描 `*.md`，gitignore 不影响 Python 扫描。

### 任务：调试检索结果

```bash
# 查看 JSON 详细结构
python knowledge/scripts/search.py "你的查询" --json --top-k 10

# 看 matched_terms 字段了解命中了哪些词
```

---

## 6. 不接受的改动

- ❌ 把 `knowledge/index.json` 加入 git（已 .gitignore）
- ❌ 把个人敏感数据提交到 `knowledge/sources/`（PR review 时会拒）
- ❌ 删除示例源（`domain-glossary.md` 等）即使觉得不实用
- ❌ 在 `knowledge/scripts/` 引入第三方依赖（破坏零依赖承诺）
- ❌ 修改 `search.py` 的 `TRIGGER_KEYWORDS` 而不在 docs 中说明

---

## 7. 进阶：触发词自定义

v1 的触发词定义在 `search.py` 的 `TRIGGER_KEYWORDS` 字典中。如果你的项目有特殊术语：

**v1 阶段**：直接编辑 `search.py` 中的 `TRIGGER_KEYWORDS`，本地使用即可（不入分发包）。

**v1.1 阶段**：迁移到 `knowledge/config.json`，build 时合并。

```json
{
  "trigger_keywords": {
    "payment-glossary": ["查支付", "支付相关"],
    "compliance-rules": ["合规", "GDPR", "PCI"]
  }
}
```

**未来**：触发词可在 Phase 0 prompt 中显式说明，由宿主自动调用 search.py。

---

## 8. 进阶：自定义 tokenizer

如果你的项目包含大量专业术语（医学 / 金融 / 法律），可能需要扩展 tokenizer：

```python
# knowledge/scripts/build_index.py 中的 _TOKEN_RE
# 当前：
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}|[0-9]+|[\u4e00-\u9fa5]+")

# 改进（示例：增加希腊字母 / 罗马数字）：
_TOKEN_RE = re.compile(
    r"[A-Za-z\u0370-\u03ff][A-Za-z0-9_\-\u0370-\u03ff]{1,}"
    r"|[0-9]+"
    r"|[\u4e00-\u9fa5]+"
)
```

修改后**必须**：

1. 在 PR 中说明动机
2. 在 `docs/architecture/knowledge-base.md` 中记录
3. 用你的样例数据验证
4. 注意：自定义 tokenizer 跨 v1.0 / v1.1 / v2 可能需要保持兼容
