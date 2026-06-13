# 如何添加知识库条目

本指南面向普通使用者。目标是让用户把资料手动喂给大模型，由大模型生成可索引 Markdown，再由本地脚本建立索引。

架构说明：[`../architecture/knowledge-base.md`](../architecture/knowledge-base.md)

---

## 推荐流程：复制模板喂给大模型

1. 打开 [`../../knowledge/llm-ingest-template.md`](../../knowledge/llm-ingest-template.md)。
2. 复制全文。
3. 把模板和你的 PRD、规范、历史用例或 API 文档一起发给大模型。
4. 要求大模型“必须输出且只输出 Markdown”。
5. 保存模型输出到 `knowledge/sources/<slug>.md`。
6. 重建索引。

```bash
python knowledge/scripts/build_index.py --rebuild
python knowledge/scripts/search.py "你的关键词"
```

如果检索能命中，生成用例时就可以说：

```text
按规范生成测试用例，参考知识库。
```

或：

```text
参考历史用例，生成登录锁定逻辑的回归用例。
```

---

## 大模型输出必须满足什么

最小结构：

```markdown
---
title: 支付规则
slug: payment-rules
category: project-conventions
tags: [payment, convention, refund]
priority: high
updated: 2026-06-13
---

# 支付规则

## 退款时效

- 已签收后 7 天内可申请退款。

---

## 来源与处理说明

- **来源**：支付 PRD
- **抽取方式**：大模型从用户资料中抽取并结构化
- **置信度**：high
- **后续维护**：无
```

`build_index.py` 会读取 `##` 章节并建立检索片段，所以重要关键词要放进二级标题或正文前部。

---

## 分类选择

| category | 适合内容 |
|---|---|
| `domain-glossary` | 术语、缩写、状态枚举、易混淆概念 |
| `project-conventions` | 命名规则、错误码、权限规则、字段规则 |
| `historical-cases` | 历史测试用例、回归用例、线上事故易漏点 |
| `compliance-rules` | 法规、合规、风控、审计要求 |
| `api-quick-ref` | API 路径、参数、响应、鉴权、错误码 |

---

## 生成用例时如何引用

检索到的知识应放进 `[参考知识]` 块：

```markdown
[参考知识]

### KB: project-conventions.md#密码强度规则
- 密码最少 8 位。
- 必须包含大写字母、小写字母、数字。
```

生成的用例必须在“追溯引用”里保留 `KB:`：

```text
REQ-AUTH-001; KB: project-conventions.md#密码强度规则
```

规则：

- 当前需求优先于知识库。
- 知识库不能覆盖用户当前需求。
- 冲突时标注 `KB 冲突`。
- 历史用例只能作为参考，不能原样复制为新用例。

---

## 可选：命令行自动录入

如果你有一个大模型包装命令，能从 STDIN 读取提示词和资料、从 STDOUT 输出 Markdown，可以使用：

```bash
set TEST_GEN_LLM_CMD=你的大模型包装命令
python knowledge/scripts/ingest.py docs/payment-spec.md
```

`ingest.py` 会调用 `prompts/knowledge_ingest_prompt.md`，自动校验 frontmatter、写入 `knowledge/sources/<slug>.md` 并重建索引。

没有包装命令时，不需要使用 `ingest.py`；手动复制 `knowledge/llm-ingest-template.md` 更简单。

---

## 常见问题

### 搜不到刚录入的内容

- 确认文件在 `knowledge/sources/`。
- 确认文件名以 `.md` 结尾。
- 确认文件名不是 `README.md`，也不是 `_` 开头。
- 运行 `python knowledge/scripts/build_index.py --rebuild`。
- 把关键词写进 `##` 标题或正文前 80 字。

### 模型输出太长

拆分为多个文件，例如：

```text
payment-glossary.md
payment-conventions.md
historical-cases-payment.md
```

### 资料里有敏感信息

先脱敏再录入。知识库不应保存密钥、Token、密码、私钥、真实银行卡号或未脱敏个人信息。
