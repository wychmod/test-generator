# Testcase Generator 知识库

知识库用来保存项目术语、项目规范、历史用例、API 速查和合规规则。生成测试用例时，大模型可以先参考这些内容，再输出带追溯引用的用例。

核心目标：用户不需要学习复杂格式，只要把资料手动喂给大模型，让大模型生成可索引 Markdown，放进 `knowledge/sources/` 后重建索引即可。

---

## 最短路径

### 1. 让大模型录入知识

复制 `knowledge/llm-ingest-template.md` 的内容，连同你的项目资料一起发给大模型。

让大模型输出可索引 Markdown。大模型会输出一个完整 Markdown 文件，形如：

```text
knowledge/sources/payment-rules.md
```

你只需要把模型输出保存到它建议的 `knowledge/sources/<slug>.md` 路径。

### 2. 建索引

```bash
python knowledge/scripts/build_index.py --rebuild
```

索引产物是 `knowledge/index.json`，它是本地生成文件，不提交、不分发。

### 3. 生成用例时说清楚要参考知识库

示例：

```text
按规范生成登录密码强度测试用例，参考知识库。
```

```text
参考历史用例，生成支付回调超时的回归用例。
```

```text
查一下知识库里的订单状态定义，再生成订单取消流程测试用例。
```

生成用例时，命中的知识会作为 `[参考知识]` 输入给阶段提示词。最终用例的“追溯引用”应包含 `KB:`，例如：

```text
REQ-AUTH-001; KB: project-conventions.md#密码强度规则
```

---

## 用户只需要记住什么

| 你想做什么 | 推荐做法 |
|---|---|
| 录入一份 PRD / 规则 / 历史用例 | 复制 `knowledge/llm-ingest-template.md` 给大模型 |
| 检查知识是否能搜到 | `python knowledge/scripts/search.py "关键词"` |
| 生成用例时参考规范 | 在请求里写“按规范”或“参考知识库” |
| 生成用例时复用历史经验 | 在请求里写“参考历史”或“查历史用例” |
| 统一术语 | 在请求里写“查术语”或“术语表” |

---

## 知识如何被生成用例阶段使用

知识库不会自动替代当前需求，它只是补充上下文。

使用规则：

- 当前用户需求优先于知识库。
- 知识库与当前需求冲突时，必须标注冲突，不得静默合并。
- 使用知识库里的规则、术语、历史用例时，必须保留 `KB:` 追溯引用。
- 只把检索命中的相关片段放入 `[参考知识]`，不要把整个知识库塞进上下文。

推荐传入格式：

```markdown
[参考知识]

### KB: project-conventions.md#密码强度规则
- 密码最少 8 位。
- 必须包含大写字母、小写字母、数字。
- 不能与最近 3 次密码相同。

### KB: historical-cases.md#TC-AUTH-LOGIN-007
- 连续 5 次输入错误密码后账号锁定 30 分钟。
- 易错点：锁定状态是否持久化、计数器是否重置。
```

---

## 目录结构

```text
knowledge/
├── README.md                    # 用户入口文档
├── llm-ingest-template.md        # 可直接复制给大模型的录入模板
├── index.json                   # 本地索引产物，忽略提交
├── sources/                     # 知识条目目录
│   ├── README.md                # sources 写法说明
│   ├── domain-glossary.md       # 示例：术语表
│   ├── project-conventions.md   # 示例：项目规范
│   └── historical-cases.md      # 示例：历史用例
└── scripts/
    ├── build_index.py           # 构建索引
    ├── search.py                # 检索知识
    └── ingest.py                # 可选：用命令行包装大模型自动写入
```

---

## 检索命令

```bash
# 首次或修改 sources 后
python knowledge/scripts/build_index.py --rebuild

# 搜索全部知识
python knowledge/scripts/search.py "密码强度"

# 搜索历史用例
python knowledge/scripts/search.py "登录失败" --source historical-cases

# 输出机器可读 JSON
python knowledge/scripts/search.py "支付回调" --json --top-k 5

# 查看触发词命中
python knowledge/scripts/search.py "按规范生成登录用例" --trigger
```

常用触发词：

| 触发词 | 主要检索内容 |
|---|---|
| `查术语` / `术语表` / `什么是` | 业务术语 |
| `按规范` / `项目规范` / `错误码` | 项目规范与约定 |
| `参考历史` / `查历史用例` / `类似用例` | 历史用例 |
| `查知识库` / `参考知识库` / `kb:` | 所有知识 |

---

## 可选：命令行自动录入

如果你已经有一个可从 STDIN 读入、从 STDOUT 输出 Markdown 的大模型命令，可以使用：

```bash
set TEST_GEN_LLM_CMD=你的大模型包装命令
python knowledge/scripts/ingest.py docs/payment-spec.md
```

`ingest.py` 会读取 `prompts/knowledge_ingest_prompt.md`，让模型抽取、分类、输出 Markdown，并自动写入 `knowledge/sources/<slug>.md` 后重建索引。

不想配置命令行时，直接使用 `knowledge/llm-ingest-template.md` 手动喂给大模型即可。

---

## 不要放进知识库的内容

- 密钥、Token、密码、私钥、真实支付卡号。
- 个人身份信息，除非已经脱敏。
- 与测试用例生成无关的长篇背景材料。
- 无法确认来源且会影响业务判断的规则。

知识库应该保存“以后生成用例会反复参考的稳定信息”，不是临时聊天记录仓库。
