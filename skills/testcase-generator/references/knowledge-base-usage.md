# 本地知识库使用指南（可选辅助层）

> **版本**: 2.3.0 | **用途**: 知识库的录入方式、检索触发词与 `[参考知识]` 消费规则
>
> 上游入口：[`../SKILL.md`](../SKILL.md) ｜ 架构与算法：[`../../../docs/architecture/knowledge-base.md`](../../../docs/architecture/knowledge-base.md)

知识库用于保存**项目级稳定信息**：术语、规范、历史用例、API 速查和合规规则。

它是**可选辅助层**：不改变六阶段主流程，只在用户明确要求"参考知识库 / 按规范 / 参考历史 / 查术语"时作为辅助上下文注入。

---

## 1. 用户录入方式

优先使用手动喂给大模型的方式：

1. 复制 `<技能根>/knowledge/llm-ingest-template.md`。
2. 把模板和项目资料一起发给大模型。
3. 让大模型输出可索引 Markdown。
4. 保存到 `<技能根>/knowledge/sources/<slug>.md`。
5. 运行 `python <技能根>/knowledge/scripts/build_index.py --rebuild`。

可选自动化方式：配置 `TEST_GEN_LLM_CMD` 后运行 `python <技能根>/knowledge/scripts/ingest.py <file>`，由脚本调用大模型、写入 sources 并重建索引。

---

## 2. 检索触发

如果当前工作目录存在 `<技能根>/knowledge/sources/*.md`，可在以下场景中显式引用知识库：

| 触发词 | 检索源 | 用途 |
|---|---|---|
| "查术语" / "术语表" / "什么是 X" | `domain-glossary` | 统一业务术语与定义 |
| "按规范" / "命名规则" / "错误码" | `project-conventions` | 项目规范与约定 |
| "参考历史" / "查历史用例" / "类似用例" | `historical-cases` | 历史用例复用与模式参考 |
| "查一下知识库" / "参考知识库" / "kb:" | 所有源 | 综合检索 |

```bash
python <技能根>/knowledge/scripts/build_index.py --rebuild
python <技能根>/knowledge/scripts/search.py "关键词"
```

---

## 3. `[参考知识]` 消费规则

命中片段应由用户或宿主在调用 Skill 时显式传入 `[参考知识]` 上下文，推荐格式：

```markdown
[参考知识]

### KB: project-conventions.md#密码强度规则
- 密码最少 8 位。
- 必须包含大写字母、小写字母、数字。

### KB: historical-cases.md#TC-AUTH-LOGIN-007
- 连续 5 次错误密码后账号锁定 30 分钟。
```

执行规则：

- 知识库不能覆盖用户当前需求；当前需求与知识库冲突时，以当前需求为准，并标注 `KB 冲突`。
- Phase 0 只识别和保留 `[参考知识]`，不把它当作用户新需求。
- Phase 1 可用 `[参考知识]` 统一术语、补充边界候选和标注规范来源。
- Phase 5 生成用例时，如果使用了知识库规则、术语或历史用例，**必须**在"追溯引用"中写 `KB:`，例如 `KB: project-conventions.md#密码强度规则`。
- 未被 `[参考知识]` 支持的推断仍必须标注为"推断"或"假设"。

---

## 4. 边界

- 知识库索引 `<技能根>/knowledge/index.json` 是**本地构建产物，不入分发包**。
- 用户后续填充的 `<技能根>/knowledge/sources/*.md` 属于个人 / 项目数据，不进分发包；仅示例源随包分发。
- 宿主不支持 Python 时，知识库检索降级为"用户手工提供术语与规范文本"。

---

*本文件由 testcase-generator v2.3.0 提供。*
