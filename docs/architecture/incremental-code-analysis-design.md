# 增量代码分析设计

> 目标：为 Phase 2 代码分析补充“只围绕本次变更和受影响范围分析”的能力设计，降低大仓库分析成本，同时避免只看 diff 导致跨文件风险漏判。

## 1. 调研结论

业界常见的增量代码分析不是单一技术，而是多种策略组合：

| 策略 | 代表实践 | 核心做法 | 适用场景 | 主要风险 |
|---|---|---|---|---|
| PR / New Code 聚焦 | SonarQube Pull Request Analysis、GitHub code scanning | 全量或近全量收集上下文，但只把新增代码、变更行或 PR 引入的问题作为门禁重点 | 代码评审、质量门禁、CI 快速反馈 | 如果仅按行过滤，可能忽略旧代码被新调用方式触发的风险 |
| Diff-aware 扫描 | Semgrep、Datadog Static Analysis | 根据 base/head diff 只扫描变更文件或变更范围，并把结果限定到 PR 相关问题 | SAST 快速扫描、规则匹配、轻量 CI | 对跨文件数据流、依赖升级、配置变更不够充分 |
| Baseline 对比 | Qodana baseline、SARIF baselineState | 保存上次结果，按稳定指纹区分 new / unchanged / updated / resolved | 遗留问题很多的项目，只拦截新增债务 | 指纹不稳定会造成误判；规则升级后基线需要重建 |
| 依赖图影响面扩展 | Bazel、Nx、Pants 等 monorepo 工具 | changed files -> owner target / project -> reverse dependencies -> affected scope | 多模块项目、monorepo、构建/测试选择 | 依赖图不完整时会漏掉动态调用、配置驱动路由 |
| 输入输出缓存 | Gradle、Bazel | 用输入、输出、工具版本和配置 hash 判断任务是否可复用 | 构建、测试、生成任务、可重复分析任务 | 非确定性输入或环境变量未入 hash 会污染缓存 |
| 语义缓存 / 增量编译 | TypeScript incremental、Roslyn incremental generators | 复用 AST、符号表、类型检查或生成步骤结果，只重算失效节点 | 强类型语言、IDE 级反馈、语义规则 | 需要维护较重的工程状态和版本兼容 |
| 增量程序分析算法 | IncA、IFDS/IDE 增量研究 | 保存分析事实和依赖关系，变更后传播失效并局部重算 | 数据流、污点分析、调用图分析 | 实现复杂，适合作为后续演进而非第一版 |

本项目更适合从“diff + baseline + 影响面扩展”的组合起步：不直接做底层静态分析引擎，而是在 Phase 2 的输入协议、Prompt 约束和产物结构里显式表达变更范围、影响范围和基线对比结果。

## 2. 本项目推荐方案

### 2.1 新增分析模式

在 Phase 2 增加两个模式：

| 模式 | 触发条件 | 说明 |
|---|---|---|
| `incremental_analysis` | 有 base/head、changed files、上一轮 Phase 2 产物或快照 | 聚焦本次变更及影响范围，结论必须标注增量来源 |
| `incremental_hybrid_analysis` | 只有 diff 或只有部分历史产物 | 能增量的部分增量分析，缺上下文的部分降级为 `hybrid_analysis` |

不建议把增量分析理解为“只看变更文件”。正确的增量边界应至少覆盖：

1. 变更行和变更文件。
2. 变更文件内的函数、类、接口、路由、schema、配置项。
3. 这些符号的直接调用方、被调用方、依赖模块、公开 API、关键数据对象。
4. 受数据库迁移、依赖版本、鉴权/路由/中间件、公共工具函数影响的扩展范围。

### 2.2 新增输入

建议 Phase 0 / Phase 2 接受以下结构化输入：

```yaml
incremental_context:
  base_ref: "main"
  head_ref: "feature/order-coupon"
  base_commit: "abc123"
  head_commit: "def456"
  diff_source: "git | user_patch | ci_provider"
  changed_files:
    - path: "src/order/coupon.py"
      status: "modified"
      added_lines: [42, 43, 44]
      deleted_lines: [39]
  diff_hunks:
    - file: "src/order/coupon.py"
      old_range: "35,12"
      new_range: "35,18"
      summary: "新增优惠券最低消费校验"
  previous_snapshot:
    path: "test-output/.cache/code-analysis/latest.json"
    required: false
  analysis_policy:
    max_impacted_files: 80
    full_scan_when_impacted_ratio_gt: 0.35
    include_reverse_dependencies: true
```

### 2.3 新增产物

在 Phase 2 增加一个前置产物：

```text
test-output/phase2/
  00_incremental_scope.md
  01_code_structure.md
  02_data_flow_analysis.md
  03_defect_radar.md
  04_concurrency_analysis.md
  05_contract_test_derivation.md
```

`00_incremental_scope.md` 应包含：

- base/head 信息。
- 变更文件列表和变更类型。
- 影响面扩展结果。
- 复用的历史分析产物。
- 被排除的文件及理由。
- 是否触发全量回退。
- 增量分析置信度和限制说明。

Phase 2 元数据建议扩展为：

```yaml
analysis_mode: incremental_analysis
base_commit: "abc123"
head_commit: "def456"
changed_files: 7
impacted_files: 23
reused_findings: 128
new_findings: 4
resolved_findings: 2
baseline_snapshot: "test-output/.cache/code-analysis/latest.json"
rules_hash: "sha256:..."
prompt_version: "2.3.0"
incremental_confidence: "high | medium | low"
fallback_reason: null
```

## 3. 分析流程

```text
输入 diff / base / head
        |
        v
变更归一化：文件状态、hunk、语言、模块、符号
        |
        v
读取历史快照：Phase 2 产物、finding 指纹、依赖图摘要
        |
        v
影响面扩展：调用关系、导入关系、路由/API、schema、配置、测试映射
        |
        v
选择策略：局部分析 / 扩展分析 / 全量回退
        |
        v
生成 Phase 2 增量产物
        |
        v
合并旧结果并标记 new / unchanged / updated / resolved / out_of_scope
```

### 3.1 变更归一化

变更文件按风险类型分桶：

| 类型 | 示例 | 默认策略 |
|---|---|---|
| 业务代码 | service、controller、repository | 分析变更符号 + 调用影响面 |
| API 契约 | OpenAPI、GraphQL、Proto | 重新推导受影响 endpoint 的契约测试 |
| 数据模型 | schema、migration、ORM model | 扩展到读写该对象的路径 |
| 公共组件 | auth、middleware、utils、validation | 扩展到所有直接调用者；超过阈值则全量回退 |
| 构建/依赖 | package lock、pom、gradle、requirements | 依赖风险扫描 + 受影响语言生态回退 |
| 配置 | env、feature flag、routing config | 标注运行时假设，扩展到相关入口 |
| 测试/文档 | tests、docs | 默认不扩大生产代码范围，但可用于回归用例推荐 |

### 3.2 影响面扩展

影响面分 4 层：

| 层级 | 名称 | 规则 |
|---|---|---|
| L0 | Diff 行 | 只覆盖新增/删除/修改行 |
| L1 | 文件内符号 | 找到变更行所在函数、类、接口、schema、endpoint |
| L2 | 直接依赖 | imports、callers、callees、route handlers、repository/model 关系 |
| L3 | 风险扩展 | 鉴权、并发、事务、缓存、消息、外部服务、公共工具调用链 |

默认推荐分析 L0-L2；当命中高风险模式时扩展到 L3。高风险模式包括：

- 鉴权、权限、登录态、租户隔离。
- 金额、库存、订单状态、支付、优惠券。
- 事务边界、锁、缓存一致性、消息幂等。
- API response schema 或错误码变更。
- 数据库 schema / migration 变更。
- 公共校验器、序列化器、异常处理器变更。

### 3.3 Baseline 合并

每条发现使用稳定指纹：

```yaml
finding_fingerprint:
  rule_id: "DEF-RACE-001"
  category: "concurrency"
  normalized_path: "src/order/coupon.py"
  symbol: "CouponService.apply_coupon"
  semantic_anchor: "min_spend check before discount"
  evidence_hash: "sha256(normalized code excerpt)"
```

合并状态：

| 状态 | 含义 |
|---|---|
| `new` | 本次增量范围内新增发现 |
| `updated` | 同一指纹仍存在，但位置或证据变化 |
| `unchanged` | 历史发现仍存在，且不属于本次门禁重点 |
| `resolved` | 历史发现消失 |
| `out_of_scope` | 历史发现存在但本次未重新验证 |

质量门禁默认只拦截 `new` 和 `updated` 的 Critical/Major 风险；`unchanged` 进入债务清单，不阻塞本次变更。

## 4. 回退策略

出现以下情况时，不应强行增量：

| 条件 | 回退模式 |
|---|---|
| 无 base/head 或 diff 不可信 | `actual_analysis` / `hybrid_analysis` |
| 无历史快照 | 首次增量可运行，但不得声明历史问题已解决 |
| 影响文件数超过阈值 | 全量 Phase 2 |
| 变更比例超过阈值 | 全量 Phase 2 |
| 规则、Prompt、模板、分析策略版本变化 | 重建 baseline |
| 依赖图构建失败 | 仅输出 L0/L1 结果，并标 `incremental_confidence: low` |
| 公共鉴权/路由/序列化层大改 | 至少扩展 L3，必要时全量 |

## 5. 缓存与快照

第一版不需要做复杂数据库，可用 JSON 快照保存必要状态：

```text
test-output/.cache/code-analysis/
  snapshots/
    main-latest.json
    feature-order-coupon-def456.json
  indexes/
    dependency-graph.json
    findings-index.json
```

快照最小字段：

```yaml
snapshot_version: 1
project_hash: "sha256(repo root + config)"
created_at: "2026-06-13T00:00:00+08:00"
commit: "abc123"
prompt_version: "2.3.0"
rules_hash: "sha256:..."
source_files:
  - path: "src/order/coupon.py"
    content_hash: "sha256:..."
    symbols:
      - name: "CouponService.apply_coupon"
        line_range: [20, 88]
findings:
  - fingerprint: "..."
    status: "open"
    severity: "major"
dependency_edges:
  - from: "src/api/order.py"
    to: "src/order/coupon.py"
    kind: "call"
```

`test-output/` 已经是本地输出目录，不进入分发包，适合放第一版缓存。后续如果希望跨 CI job 复用，可把该目录作为 CI cache artifact。

## 6. 与现有流水线的集成

### 6.1 Phase 0

Phase 0 负责识别输入是否包含 diff / PR / commit 信息，并输出：

- 输入是否可做增量。
- 缺失的 base/head 或历史快照。
- 初步变更摘要。
- 是否需要用户补充仓库路径、commit 或 patch。

### 6.2 Phase 2

Phase 2 增加“增量范围界定”步骤，先产出 `00_incremental_scope.md`，再生成现有结构分析、数据流、缺陷雷达、并发分析、契约测试推导。

现有 `source_files` 字段保留，但需要区分：

```yaml
source_files:
  changed: []
  impacted: []
  reused_from_baseline: []
  excluded: []
```

### 6.3 Phase 5

用例生成阶段优先生成：

- 覆盖新增风险的回归用例。
- 覆盖变更 API 契约的接口用例。
- 覆盖受影响状态迁移的最小路径集。
- 覆盖 `resolved` 缺陷的防回归用例。

## 7. 推荐落地路线

### v1：Prompt 和产物协议增量化

- 在 `skills/testcase-generator/prompts/phase2_code_analysis_prompt.md` 增加 `incremental_analysis` / `incremental_hybrid_analysis`。
- 增加 `00_incremental_scope.md` 产物模板。
- 在质量门禁中要求增量分析必须说明 base/head、影响面和回退原因。

### v2：轻量脚本辅助

- 新增脚本读取 `git diff --name-status`、`git diff --unified=0`。
- 输出 `incremental_context.json` 供 Phase 0 / Phase 2 使用。
- 基于文件导入关系和常见框架路径生成 L1/L2 影响面。

### v3：快照和指纹合并

- 保存 Phase 2 findings snapshot。
- 实现 finding 指纹稳定化。
- 输出 new / updated / unchanged / resolved。

### v4：语言级语义增强

- 针对 Python / JavaScript / TypeScript / Java 分别补充轻量 AST 解析。
- 对 API、schema、路由、ORM、调用关系做更准确的符号映射。
- 对高风险路径做局部数据流追踪。

## 8. 质量要求

增量分析产物必须满足：

1. 不能只给 changed files，必须说明是否做过影响面扩展。
2. 所有增量结论必须能追溯到 diff、baseline 或影响面规则。
3. 未重新验证的历史发现必须标 `out_of_scope`，不能默认为已解决。
4. baseline 不匹配时必须回退或重建，不能复用。
5. `incremental_confidence: low` 时，后续 Phase 5 必须提示测试覆盖风险。

## 9. 调研来源

- SonarQube Server Pull Request Analysis：<https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/pull-request-analysis/introduction/>
- SonarQube New Code / Clean as You Code：<https://docs.sonarsource.com/sonarqube-server/user-guide/about-new-code>
- GitHub code scanning on pull requests：<https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/triage-alerts-in-pull-requests>
- Semgrep CI diff-aware scanning：<https://semgrep.dev/docs/kb/semgrep-ci/trigger-diff-scans-env-var>
- Semgrep CI environment variables for diff scans：<https://docs.semgrep.dev/semgrep-ci/ci-environment-variables>
- Datadog Static Analysis diff-aware scanning：<https://docs.datadoghq.com/security/code_security/static_analysis/setup/>
- JetBrains Qodana baseline：<https://www.jetbrains.com/help/qodana/baseline.html>
- SARIF baseline states：<https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html>
- Bazel concepts: dependencies and action cache：<https://github.com/bazelbuild/bazel/blob/master/site/en/concepts/build-ref.md>
- Gradle incremental build：<https://docs.gradle.org/current/userguide/incremental_build.html>
- Nx affected commands：<https://nx.dev/ci/features/affected>
- TypeScript incremental builds：<https://www.typescriptlang.org/tsconfig/incremental.html>
- Roslyn incremental generators cookbook：<https://github.com/dotnet/roslyn/blob/main/docs/features/incremental-generators.cookbook.md>
- IncA incremental program analysis paper：<https://arxiv.org/abs/1808.05843>
