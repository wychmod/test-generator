# 知识库架构（v1 — 触发式 BM25）

> 目的：在不改六阶段流水线主流程的前提下，让 Skill 在生成用例时能够参考项目级知识。
>
> 用户文档：[`../../knowledge/README.md`](../../knowledge/README.md)
>
> 贡献指南：[`../development/adding-knowledge.md`](../development/adding-knowledge.md)
>
> 流水线全景：[`pipeline-overview.md`](pipeline-overview.md)

---

## 1. 设计原则

| 原则 | 选择 | 反例（不选的理由） |
|---|---|---|
| **零外部依赖** | BM25 + 自写 tokenizer | RAG 需要 Embedding API 或本地向量库，破坏跨宿主一致性 |
| **本地优先** | Markdown 文件 + JSON 索引 | 远程 KB 需要网络，不适合 Skill 分发 |
| **触发式注入** | 用户显式说"参考历史/查术语"才查 | 全局注入会污染 context、且无法控制敏感数据外泄 |
| **可审计** | 索引 JSON 透明、可 git diff | 向量数据库不透明，难复现 |
| **可分发** | 示例源进 `.skill`/`.zip`，用户内容不进 | ChromaDB 二进制 index 不便分发 |

**为什么不直接做 Embedding/RAG？** 见后文 §7 演进路径。

---

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 用户输入                                                                  │
│   "按规范生成密码强度规则的测试用例"                                        │
│           │                                                              │
│           ▼                                                              │
│   ┌──────────────────────────────────┐                                    │
│   │ Phase 0 输入预处理               │                                    │
│   │  ├─ 触发词检测                  │──命中"按规范"──► knowledge/scripts  │
│   │  └─ [可选] 调用 search.py        │                  /search.py       │
│   └──────────────────────────────────┘                       │           │
│           │ 检索结果注入 [参考知识]                              │           │
│           ▼                                                  ▼           │
│   ┌──────────────────────────────────┐      ┌──────────────────────┐    │
│   │ Phase 1 需求分析                │      │ knowledge/index.json │    │
│   │ ...                             │      │   ├─ sources[]       │    │
│   │ (引用 [参考知识] 中的术语/规范)  │      │   ├─ inverted_index  │    │
│   └──────────────────────────────────┘      │   └─ bm25_stats      │    │
│           │                                └──────────────────────┘    │
│           ▼                                          ▲                  │
│   ┌──────────────────────────────────┐            │                   │
│   │ Phase 5 用例生成                │            │ 构建               │
│   │ (引用 [参考知识] 中的历史用例)   │      ┌─────┴───────────┐        │
│   └──────────────────────────────────┘      │ build_index.py  │        │
│                                              │ (扫描 sources/  │        │
│                                              │  输出 index.json)│       │
│                                              └─────────────────┘        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 触发词 → 知识源映射

`search.py` 内置的 `TRIGGER_KEYWORDS` 字典：

| 知识源 | 触发词 |
|---|---|
| `domain-glossary` | 术语表 / 术语 / 查术语 / glossary / 什么是 / 定义 / 名词解释 / 业务概念 |
| `project-conventions` | 按规范 / 项目规范 / 规范 / 命名规则 / 命名规范 / convention / 标准 / 约定 / 错误码 |
| `historical-cases` | 参考历史 / 查历史 / 查历史用例 / 历史用例 / 类似用例 / 复用 / 历史 / 回归用例 / 已有用例 / historical |
| `*`（所有源） | 查一下知识库 / 查知识库 / 搜知识库 / 知识库里 / knowledge base / kb: / /kb |

**v1 现状**：Phase prompt 还没自动识别触发词（属于 P3 范围）。当前使用方式：
1. 宿主/用户手动调用 `python knowledge/scripts/search.py "..."`
2. 把命中片段作为补充输入传给 Skill

**P3 计划**：在 `prompts/phase0_input_preprocessing_prompt.md`、`phase1_requirements_prompt.md`、`phase5_testcase_generation_prompt.md` 中显式加入"如命中知识库，注入 [参考知识] 上下文"的指令。

---

## 4. 检索算法：BM25

### 4.1 为什么选 BM25

| 维度 | BM25 | Embedding |
|---|---|---|
| 依赖 | 零 | 必须 Embedding API 或本地模型 |
| 跨宿主一致性 | 完全一致（同输入同输出） | 取决于模型，不同宿主可能漂移 |
| 可解释性 | 高（看得见的 TF-IDF 分数） | 低（黑盒向量） |
| 速度 | < 50ms（千级文档） | 100ms+（含 Embedding） |
| 中文处理 | 自写 `[\u4e00-\u9fa5]+` tokenizer | 需 jieba 等 |
| 测试用例场景 | TC-ID / 关键词命中是强信号 | 语义模糊可能反而降低精度 |

**结论**：测试用例生成场景里，BM25 在零依赖前提下已足够好。

### 4.2 算法实现

**位置**：[`../../knowledge/scripts/build_index.py`](../../knowledge/scripts/build_index.py) 和 `search.py`

**关键参数**（Robertson / Zaragoza 2009 默认）：

- `k1 = 1.2`（词频饱和度）
- `b = 0.75`（文档长度归一化强度）

**优先级加权**：

```python
PRIORITY_WEIGHT = {"high": 1.5, "normal": 1.0, "low": 0.7}

# 最终得分 = BM25 原始分数 × priority_weight
```

**索引格式**（`index.json`）：

```json
{
  "version": 1,
  "built_at": "2026-06-13T...",
  "sources": [...],
  "inverted_index": {
    "term_freq": {"file.md#0": {"token": count, ...}, ...},
    "doc_freq":  {"token": doc_count, ...},
    "doc_len":   {"file.md#0": token_count, ...},
    "avg_doc_len": 22.59,
    "k1": 1.2,
    "b": 0.75
  },
  "stats": {"num_sources": 3, "num_sections": 17, ...}
}
```

---

## 5. 增量构建

```bash
python knowledge/scripts/build_index.py                # 仅在源变化时重建
python knowledge/scripts/build_index.py --rebuild      # 强制重建
python knowledge/scripts/build_index.py --stats        # 看索引统计
```

**变更检测**：基于源文件的 `mtime` + `sha256`，自动跳过未变化的文件。

**索引不入 git**（已在 `.gitignore`）：

```gitignore
/knowledge/index.json
```

理由：

- 跨机器 `mtime` 不同步（git clone 后需要本地重建）
- 可能包含项目敏感数据
- 几十 KB，每次 commit 没意义

---

## 6. 与 Skill 分发的关系

### 6.1 进分发包的部分

- ✅ `knowledge/README.md`（用户文档）
- ✅ `knowledge/sources/*.md`（**示例源**：`domain-glossary.md`、`project-conventions.md`、`historical-cases.md`）
- ✅ `knowledge/sources/README.md`（使用说明）
- ✅ `knowledge/scripts/build_index.py`（构建工具）
- ✅ `knowledge/scripts/search.py`（检索工具）

### 6.2 不进分发包的部分

- ❌ `knowledge/index.json`（本地构建产物）
- ❌ 用户后续添加的所有 `.md`（属于个人/项目，不应分发）

### 6.3 manifest 同步点

`skill.manifest.json` 中：

- `运行时文件` 列表追加 `knowledge/README.md`、`knowledge/sources/**`、`knowledge/scripts/**`
- `分发排除` 列表追加 `knowledge/index.json`

---

## 7. 演进路径

### v1（当前）✅

- 触发词 + BM25 + 本地 Markdown
- 手动调用 search.py，复制结果给 Skill

### v1.1（短期） — Phase 集成

- 在 `prompts/phase0/1/5` 中加入知识库感知指令
- 提供 `knowledge/scripts/inject.py`：自动检测触发词 + 检索 + 格式化为 `[参考知识]` 块
- 评测：在 test-fixtures 加"知识库感知"测试用例

### v2（中长期） — 语义检索 + 混合

- 引入 Embedding（用户自选 OpenAI / Cohere / 本地模型）
- 混合检索：BM25 分数 + 向量相似度 = 加权和
- 跨语言：英文文档与中文查询互译检索

### v3（远期） — MCP 桥接

- 把本地知识库暴露为 MCP Server
- 让任何宿主（Claude / Cursor / Codex）通过 MCP 协议检索
- 保持本地存储 + 触发可控

### 不做的事

- ❌ 不做自动全量索引（保留触发式可控性）
- ❌ 不做远程知识库（破坏"零依赖"承诺）
- ❌ 不做隐式注入（保护用户隐私）
- ❌ 不强依赖 Embedding（保留 BM25 兜底）

---

## 8. 评测与健康度

### 8.1 基础健康度检查

```bash
python knowledge/scripts/build_index.py --stats
# 期望：sources ≥ 1, sections ≥ 1, vocab ≥ 10
```

### 8.2 检索质量自检

`docs/quality/test-plan.md` 中可补充一组知识库相关评测：

| 输入 | 期望命中源 | 期望 top-1 heading |
|---|---|---|
| "SKU" | domain-glossary | 支付相关术语 |
| "密码强度" | project-conventions | 密码强度规则 |
| "登录失败" | historical-cases | TC-AUTH-LOGIN-* |
| "退款" | historical-cases | TC-PAY-ALIPAY-* |

### 8.3 失败模式

| 症状 | 原因 | 修复 |
|---|---|---|
| 检索返回 0 结果 | 索引未构建或源为空 | 跑 `build_index.py` |
| 检索命中但 matched 为空 | heading 含关键词但 body 没 | 正常，snippet 仍可用 |
| 索引过大（> 10MB） | 源过多或单个文件过大 | 拆分源、删除冗余 |
| 跨机器索引不一致 | mtime 漂移 | 删除 index.json 后重建 |

---

## 9. 与现有 v2.1.0 能力的边界

| 能力 | 来源 | 与知识库的关系 |
|---|---|---|
| 输入质量预处理 | Phase 0 | Phase 0 命中触发词后调用知识库检索 |
| 可测试需求抽取 | Phase 1 | 检索结果作为 `[参考知识]` 上下文 |
| 代码分析 | Phase 2 | 不涉及（代码分析基于源码，不基于业务知识） |
| 领域建模 | Phase 3 | 可参考历史用例的命名约定 |
| MBT 设计 | Phase 4 | 可参考历史状态机模板 |
| 用例生成 | Phase 5 | 检索结果作为 `[参考用例]` 注入 |

**结论**：知识库是 Skill 的**辅助层**，不改变六阶段主流程。
