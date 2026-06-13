# Testcase Generator 知识库（v1）

> 目的：让 testcase-generator 在生成测试用例时能够参考**项目级知识**（术语表、历史用例、规范条款），而不是从零开始。
>
> 设计原则：**触发式检索**，**本地 Markdown**，**零外部依赖**，**跨宿主一致**。
>
> 架构详解：[`../docs/architecture/knowledge-base.md`](../docs/architecture/knowledge-base.md)
>
> 如何添加知识：[`../docs/development/adding-knowledge.md`](../docs/development/adding-knowledge.md)

---

## 工作原理（一句话）

当用户在 Skill 输入中包含**触发词**（如"参考历史"、"查一下"、"按规范"），Skill 会自动从 `knowledge/sources/` 中检索相关片段，作为 `[参考知识]` 注入到 Phase 0/1/5 的 prompt 中。

没有触发词 → 知识库不参与 → 与 v2.1.0 行为完全一致。

---

## 目录结构

```
knowledge/
├── README.md                       ← 本文件（用户文档）
├── SKILL.md                        ← 知识库子 Skill 入口（分发包内）
├── index.json                      ← 索引产物（git ignore，本地构建）
├── sources/                        ← 实际知识源（用户填充，分发包带示例）
│   ├── README.md                   ← sources 使用说明
│   ├── domain-glossary.md          ← 🆕 示例：业务术语表
│   ├── project-conventions.md      ← 🆕 示例：项目规范
│   └── historical-cases.md         ← 🆕 示例：历史用例集
└── scripts/
    ├── build_index.py              ← 构建索引（不依赖外部库）
    └── search.py                   ← BM25 检索
```

---

## 快速上手

### 1. 首次使用：构建索引

```bash
python knowledge/scripts/build_index.py
```

输出：`knowledge/index.json`（约几十 KB）

### 2. 检索知识

```bash
# 关键词检索
python knowledge/scripts/search.py "登录失败"

# 多关键词
python knowledge/scripts/search.py "用户认证 token 过期"

# 限定来源
python knowledge/scripts/search.py "退款流程" --source historical-cases

# 显示 Top-K
python knowledge/scripts/search.py "密码强度" --top-k 5
```

### 3. 在 Skill 中使用

| 触发词 | 含义 |
|---|---|
| `参考历史` / `查历史用例` | 检索 `historical-cases` 源 |
| `按规范` / `按规范生成` | 检索 `project-conventions` 源 |
| `术语表` / `查术语` | 检索 `domain-glossary` 源 |
| `查一下知识库` / `知识库` | 跨所有来源检索 |

更多触发词可自定义（见 `search.py` 中 `TRIGGER_KEYWORDS`）。

### 4. 添加新知识

把 `.md` 文件放到 `sources/` 目录，重建索引：

```bash
# 添加文件
cp your-glossary.md knowledge/sources/custom-glossary.md

# 重建索引
python knowledge/scripts/build_index.py --rebuild
```

格式要求：见 [`../docs/development/adding-knowledge.md`](../docs/development/adding-knowledge.md)。

---

## 索引产物（`index.json`）

- **不入 git**（已在 `.gitignore`）
- 本地构建，可随时 `build_index.py --rebuild`
- 格式：`{ "sources": {...}, "terms": {...}, "doc_freq": {...}, "doc_len": {...} }`
- 体积：~几十 KB（与文档数量成正比）

---

## 隐私与边界

- ✅ **完全本地**：不联网，不上传知识库内容
- ✅ **不进分发包**：示例源进入 `.skill`/`.zip`，但用户填充内容**不进入**
- ❌ **不主动注入**：必须显式触发词才检索
- ❌ **不调用 Embedding**：不依赖任何 LLM API / 外部服务

---

## 与 Phase 0/1/5 的集成（v1 阶段说明）

本轮交付（P1+P2）：**脚手架 + 检索工具就绪**。

Phase 集成（P3）的具体做法留给下一轮：在 `prompts/phase0_input_preprocessing_prompt.md`、`phase1_requirements_prompt.md`、`phase5_testcase_generation_prompt.md` 中显式加入"如命中知识库，注入 `[参考知识]` 上下文"的指令。

当前 v1 的使用方式：用户在调用 Skill 时手动添加触发词，宿主或用户自己运行 `search.py` 检索，把命中片段作为补充输入传入 Skill。

---

## 不做的事（明确边界）

- ❌ 不做 Embedding / 向量检索（避免外部 API 依赖）
- ❌ 不做自动触发（保持显式可控）
- ❌ 不存储敏感数据（用户自负责任，建议加密或本地存储）
- ❌ 不修改 Phase 0/1/5 的产物协议（v1 阶段保持兼容）
