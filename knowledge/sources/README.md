# knowledge/ — 本地知识库源目录

把你的项目知识放到这里。每个 `.md` 文件会被自动索引，在 Skill 触发相关检索时被检索命中。

## 文件命名约定

- 小写 + 连字符：`user-auth-rules.md`、`payment-glossary.md`
- 一个文件 = 一个主题（避免大杂烩）
- 文件名会被作为来源标识出现在检索结果中（`source: <文件名>`）

## 文件格式

最简格式即可：纯 Markdown，**不需要 frontmatter**。如果想附加元数据，可选顶部 YAML：

```markdown
---
title: 用户认证业务术语表
tags: [auth, user, glossary]
priority: high   # high / normal / low
updated: 2026-06-13
---

# 内容正文...
```

### 优先级影响检索权重

- `priority: high` → 检索得分 ×1.5
- `priority: normal`（默认）→ 检索得分 ×1.0
- `priority: low` → 检索得分 ×0.7

## 内容建议

| 类型 | 适合放在 | 示例 |
|---|---|---|
| 业务术语表 | `domain-glossary.md` | "什么是 SKU"、"订单状态枚举值" |
| 项目规范 | `project-conventions.md` | "命名规则"、"错误码约定" |
| 历史用例 | `historical-cases.md` | "已通过的回归用例"、"易漏场景" |
| 合规条款 | `compliance-rules.md` | "支付合规要求"、"GDPR 条款" |
| API 文档 | `api-quick-ref.md` | "接口参数说明"、"错误响应格式" |

## 不要放什么

- ❌ 密钥 / 凭证 / PII
- ❌ 超过 1MB 的单个文件（影响检索性能）
- ❌ 截图 / 二进制（用文字描述或外链）
- ❌ 与测试用例生成无关的内容

## 重建索引

```bash
python knowledge/scripts/build_index.py --rebuild
```

检测到文件变化（mtime）会自动重建；强制重建用 `--rebuild`。
