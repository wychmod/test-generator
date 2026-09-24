# 大模型知识库录入模板

把本文件完整复制给大模型，然后把你的项目资料粘贴到最后的“待录入资料”区域。大模型应输出一个可保存到 `<技能根>/knowledge/sources/<slug>.md` 的 Markdown 文件。

> **路径约定**：本文中的 `<技能根>` 指技能目录 `skills/testcase-generator/`。激活到宿主后，它就是宿主技能目录（如 `.claude/skills/testcase-generator/`）。

---

## 给大模型的指令

你是测试用例生成器的知识库录入员。请把以下资料录入知识库，用于后续生成测试用例时参考。

你的任务：

1. 从资料中抽取稳定、可复用、会影响测试设计的信息。
2. 判断知识类别：术语表、项目规范、历史用例、合规规则或 API 速查。
3. 输出可直接被 BM25 索引的 Markdown。
4. 保留来源、限定词、错误码、状态码、阈值、枚举值和时间窗口。
5. 不要编造资料中不存在的业务规则。

必须输出且只输出 Markdown。不要解释你的处理过程，不要输出寒暄文字。

建议保存路径：

```text
<技能根>/knowledge/sources/<slug>.md
```

---

## 输出格式

```markdown
---
title: <清晰标题>
slug: <英文小写短横线命名，例如 payment-rules>
category: <domain-glossary | project-conventions | historical-cases | compliance-rules | api-quick-ref>
tags: [<3-5 个关键词>]
priority: <high | normal | low>
source_type: <prd | markdown | text | pasted | api_spec | other>
source_origin: <资料来源，例如 文件名 / 用户粘贴 / URL>
updated: <YYYY-MM-DD>
---

# <清晰标题>

## <知识点 1>

<结构化内容。优先使用表格、短列表、编号步骤。>

## <知识点 2>

<结构化内容。>

---

## 来源与处理说明

- **来源**：<资料来源>
- **抽取方式**：大模型从用户提供资料中抽取并结构化
- **置信度**：<high | medium | low>
- **敏感信息处理**：<无 / 已脱敏 / 已跳过>
- **后续维护**：<需要人工补充或确认的事项；没有则写“无”>
```

---

## 分类规则

| 资料主要内容 | category | 文件名建议 |
|---|---|---|
| 名词解释、缩写、状态枚举、易混淆概念 | `domain-glossary` | `<domain>-glossary.md` |
| 命名规则、错误码、权限规则、字段规则、测试规范 | `project-conventions` | `<domain>-conventions.md` |
| 已有测试用例、回归场景、线上事故、易漏点 | `historical-cases` | `historical-cases-<module>.md` |
| 法规、合规、风控、审计要求 | `compliance-rules` | `compliance-<topic>.md` |
| API 端点、参数、响应、错误码、鉴权方式 | `api-quick-ref` | `api-<module>.md` |

---

## 抽取要求

必须保留：

- 数值阈值，例如 `>= 8 位`、`5 次`、`30 分钟`。
- 状态枚举和合法状态流转。
- 错误码、HTTP 状态码、接口路径、字段名。
- “必须”“不允许”“仅”“除非”等关键限定词。
- 历史用例中的前置条件、步骤、预期结果和易错点。

必须标注：

- `[推断: 依据]`：资料没有直接说明，但可以从上下文合理推断。
- `[冲突: 描述]`：资料内部存在矛盾。
- `[需确认: 问题]`：缺少影响测试设计的关键信息。
- `[已脱敏: 类型]`：发现敏感信息并脱敏。

禁止：

- 编造新的业务规则。
- 删除关键边界条件。
- 输出大段背景叙事。
- 写入密钥、密码、Token、私钥、真实银行卡号或未脱敏个人信息。

---

## 待录入资料

```text
在这里粘贴 PRD、规范、历史用例、API 文档、会议纪要或其他项目资料。
```
