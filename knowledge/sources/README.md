# knowledge/sources 使用说明

这里存放真正会被检索的知识条目。每个 `.md` 文件都会被 `build_index.py` 切成章节并写入 `knowledge/index.json`。

普通用户优先使用 `../llm-ingest-template.md`：把模板和项目资料一起发给大模型，让大模型输出完整 Markdown，再保存到本目录。

---

## 最小可用格式

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
- 超过 7 天后只能由客服后台发起特殊退款。

## 支付回调

- 支付回调必须做幂等处理。
- 第三方回调失败时，系统 5 分钟后轮询交易状态。

---

## 来源与处理说明

- **来源**：支付 PRD
- **抽取方式**：大模型从用户资料中抽取并结构化
- **置信度**：high
- **后续维护**：无
```

---

## 文件怎么命名

- 使用英文小写和短横线：`payment-rules.md`、`auth-glossary.md`。
- 一个文件只放一个主题，避免 `all-in-one.md`。
- 历史用例按模块拆分：`historical-cases-auth.md`、`historical-cases-payment.md`。
- 临时禁用文件时，在文件名前加 `_`，例如 `_old-payment-rules.md`。索引构建会跳过 `_` 开头的文件。

---

## 哪些内容适合放进来

| 类型 | 示例 |
|---|---|
| 业务术语 | SKU、会员等级、订单状态、退款窗口 |
| 项目规范 | ID 命名、错误码、权限规则、密码强度 |
| 历史用例 | 已验证回归用例、线上事故回归点、易漏场景 |
| API 速查 | 路径、参数、响应 Schema、错误响应 |
| 合规规则 | 数据保留、支付合规、审计要求 |

---

## 哪些内容不要放进来

- 密钥、Token、密码、私钥。
- 真实身份证、手机号、银行卡号等个人敏感信息。
- 临时讨论中尚未确认的猜测。
- 大段背景材料、会议寒暄、与测试设计无关的信息。

---

## 检索效果写法建议

BM25 更依赖关键词命中。为了让检索更稳定：

- 把关键词放在 `##` 标题中，例如 `## 密码强度规则`。
- 重要术语在正文中自然出现 2-3 次。
- 历史用例标题保留用例 ID，例如 `## TC-AUTH-LOGIN-007 - 密码错误 5 次锁定`。
- 规则尽量写成短句或表格，不要只写长段落。

---

## 重建和验证

```bash
python knowledge/scripts/build_index.py --rebuild
python knowledge/scripts/search.py "你的关键词"
```

如果搜索不到：

- 确认文件在 `knowledge/sources/` 下。
- 确认文件名以 `.md` 结尾。
- 确认文件名不是 `README.md`，也不是 `_` 开头。
- 确认关键词出现在标题或正文里。
