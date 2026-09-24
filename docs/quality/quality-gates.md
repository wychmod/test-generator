# 阶段间质量门禁（Quality Gates）

> 目的：把 `skills/testcase-generator/resources/quality_checklist.md` 中分散在各 Phase 的检查项，抽取为一份「门禁决策表」——告诉流水线执行者每个阶段什么时候可以放行、什么时候必须修复后重审、什么时候必须降级。
>
> 详细检查项与权重：[`../../skills/testcase-generator/resources/quality_checklist.md`](../../skills/testcase-generator/resources/quality_checklist.md)（v2.3.0，ISTQB + ISO/IEC/IEEE 29119-3:2021 + CMMI DEV 3.0）
>
> 下表用 `G<阶段>-<组>` 引用 `quality_checklist.md` 中的检查组；该文件的检查组标题写作
> `G<阶段>.<组>`（如 `G2.1`），检查项 ID 写作 `G<阶段>-<组>-<序号>`（如 `G2-1-1`），
> 三者指同一组。
>
> 流水线结构：[`../architecture/pipeline-overview.md`](../architecture/pipeline-overview.md)
>
> 评测维度：[`test-plan.md`](test-plan.md)

---

## 1. 门禁模型

每个阶段结束后执行门禁评估，得分 ≥ **B 级（80 分）** 才能进入下一阶段。

```
                         ┌──────────────┐
Phase N 输出 ──────►     │  门禁评估    │
                         │  (Gx 检查)   │
                         └──────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
          Score ≥ 90      80 ≤ Score < 90   Score < 80
          (A 级，Pass)    (B 级，Warn)     (C/D，Fail)
                │               │               │
                ▼               ▼               ▼
        进入 Phase N+1    修复 Warning      必须修复后
        (直接放行)        后进入 N+1        重新审核
```

**Score 等级定义**（来自 `quality_checklist.md`）：

| 等级 | 分数 | 含义 | 行动 |
|---|---|---|---|
| 🟢 A | 90-100 | 超出预期 | 直接进入下一阶段 |
| 🟡 B | 80-89 | 达标，有小瑕疵 | 修复 Warning 后进入 |
| 🟠 C | 70-79 | 基本合格，需改进 | 修复所有 Warning 和 Minor |
| 🔴 D | < 70 | 不达标 | 必须修复后重新审核 |

---

## 2. 各阶段门禁摘要

### 2.1 G0 — Phase 0 输入预处理门禁

**权重分配**：输入质量 30% / 假设与降级 30% / 可追溯性 40%

**放行条件（A 或 B 级）**：
- G0-1：输入类型识别明确、无乱码、关键字段可被引用
- G0-2：所有假设显式标注、降级路径合理、继续条件清晰
- G0-3：来源引用保留、术语规范化、风险摘要完整

**阻断规则**（无论得分多高，必须阻断）：
- 发现关键规则互相冲突且无仲裁依据
- 验收标准不可判定（"合理/适当/良好"等主观词）
- 状态机不闭合
- 关键字段全部缺失且无任何推断依据

**降级路径**（不通过门禁时）：
- 阻断项轻微 → 继续 Phase 1，但所有推断标 [假设]，最终产物降级为「草稿」
- 阻断项中等 → 跳过 Phase 2-4，只输出 Phase 1 的测试点清单
- 阻断项严重 → 停止流水线，要求用户补充输入

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-0输入预处理---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

### 2.2 G1 — Phase 1 需求分析门禁

**权重分配**：完整性 25% / 准确性 25% / 可测试性 25% / 一致性 15% / 幻觉防护 10%

**放行条件**：
- G1：所有明确功能点已提取为 REQ；用户角色识别完整；主流程+关键子流程建模
- G2：结构化重述与原意一致；边界值有依据；等价类无重叠无遗漏
- G3：AC 二元化率 > 90%；预期结果可机器验证；测试数据可构造
- G4：ID 格式统一唯一；术语全局一致；模板格式合规
- G5：每条 REQ 可追溯到原始输入；[推断] 标注比例合理

**必须警告（即使通过也需标记）**：
- AC 二元化率 < 95%（提示存在主观词）
- 等价类存在重叠或遗漏
- 任何一条 REQ 无 AC

**阻断规则**：
- 平均每条 REQ < 1 条 AC
- 存在凭空创造的功能点（无来源且非推断）
- 同一概念术语不一致且影响追溯

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-1需求分析---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

### 2.3 G2 — Phase 2 代码分析门禁

**权重分配**：分析范围 20% / 数据流控制流 25% / 缺陷识别 25% / 需求对齐 20% / 幻觉防护 10%

**放行条件**：
- G2-1：公开接口覆盖率 = 100%；关键私有函数已分析；外部依赖清单完整
- G2-2：DFD Level-0 完整；分支覆盖全；异常传播链已绘制
- G2-3：每条 DEF 有代码依据 + CWE 分类；严重性评估合理；修复建议可行
- G2-4：需求-代码映射率 ≥ 90%；代码实现与需求差异已记录
- G2-5：分析模式已声明（actual/contract/requirements_only）；[推断] 比例 < 40%

**必须警告**：
- 出现"可能存在…但无法确认"的模糊描述
- Critical DEF 无修复建议
- 需求-代码映射率 < 95%

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-2代码分析---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

### 2.4 G3 — Phase 3 领域建模门禁

**权重分配**：ERD 25% / 状态机 30% / 参数空间 25% / 跨阶段一致性 20%

**放行条件**：
- G3-1：核心实体完整、关系基数正确、无孤立实体、ERD 图文一致
- G3-2：**状态机完备性是硬指标**
  - 除 Initial 外每个状态至少有一个入边（权重 5）
  - 除 Final 外每个状态至少有一个出边（权重 5）
  - 无孤立状态（权重 5）
  - 无不可达状态（权重 4）
  - Choice 守卫条件互斥且布尔空间完备（权重 5）
  - Initial 恰好 1 个（权重 2）
- G3-3：参数枚举完整；值域明确；特殊值（Null/Empty/SpecialChar/Unicode/Overflow）已列入
- G3-4：实体↔需求、状态↔需求/代码、参数↔边界条件 三类追溯均完整

**阻断规则**：
- 存在死状态（无出边且非 Final）
- 存在孤立状态（无入边且非 Initial）
- 状态总数 ≥ 50 且未应用任何优化策略
- 跨阶段术语不一致且影响后续 MBT 推导

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-3领域建模---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

### 2.5 G4 — Phase 4 MBT 设计门禁

**权重分配**：模型正确性 30% / 覆盖准则 25% / 可操作性 25% / 模型优化 20%

**放行条件**：
- G4-1：测试模型是业务模型的有效子集（状态⊆业务状态、转换⊆业务转换、守卫不弱化）
- G4-2：覆盖目标量化（百分比或数量）；MTS ≤ 全路径 × 0.5；高风险路径优先；单点覆盖 < 30%
- G4-3：每个路径可转化为用例；前置条件充分；Smoke/Critical/Standard/Full 分层清晰
- G4-4：状态爆炸已控制；所有简化/合并/抽象决策有理由；模型变更记录完整

**阻断规则**：
- 测试转换出现业务模型中没有的新转换
- 守卫条件弱化（漏掉业务约束）
- MTS 大小 > 全路径 × 0.5 且无压缩策略

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-4mbt-设计---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

### 2.6 G5 — Phase 5 用例生成门禁（最终）

**权重分配**：覆盖完整性 30% / 用例质量 30% / 去重优化 20% / 自动化就绪 10% / 规范性 10%

**硬性放行条件**：
- G5-1：需求覆盖率 = 100%；边界条件覆盖率 = 100%；追溯矩阵闭合（正逆向均无断裂）
- G5-2：标题唯一清晰；前置条件充分；步骤可执行；输入数据明确；预期结果二元化
- G5-3：去重完成（无完全相同 + 无 > 85% 相似度重复）
- G5-5：TC-ID 全局唯一

**必须警告**：
- 自动化就绪率 < 70%
- 用例平均步骤数不在 3-8 最优区间
- 优先级分布不符合风险画像

**阻断规则**：
- 任何一条 REQ 无对应 TC
- 关键校验/异常/权限拒绝/非法状态流转无负向用例
- Critical/Major DEF 无反向测试 TC
- 追溯矩阵存在断裂（不可双向追溯）

详见：[`../../skills/testcase-generator/resources/quality_checklist.md#phase-5用例生成---质量门禁`](../../skills/testcase-generator/resources/quality_checklist.md)

---

## 3. 综合评分公式

```
Overall_Quality = 
  0.15 × Phase0_Score +
  0.17 × Phase1_Score +
  0.17 × Phase2_Score +
  0.17 × Phase3_Score +
  0.17 × Phase4_Score +
  0.17 × Phase5_Score
```

每个 `Phase_Score`：

```
Phase_Score = Σ(Check_Item_Weight × Item_Pass_Status) / Σ(All_Weights)

Item_Pass_Status = 1.0 (Pass)
                = 0.7 (Pass with Warning)
                = 0.3 (Fail with Workaround)
                = 0.0 (Fail)
```

---

## 4. 通用度量指标基线

下表是跨阶段通用的健康指标。每次交付时应同步产出：

| 指标 | 计算 | 目标 | 严重 | 危险 |
|---|---|---|---|---|
| 需求覆盖率 | Covered_REQs / Total_REQs | 100% | < 95% | < 90% |
| 边界覆盖率 | Covered_BVPoints / Total_BVPoints | 100% | < 95% | < 90% |
| 路径覆盖率 | Covered_PATHs / Total_MTS_PATHs | ≥ 目标 | -10% | -20% |
| 用例有效率 | Unique_TCs / Total_TCs | > 85% | < 75% | < 60% |
| 幻觉率 | Unfounded_Items / Total_Items | < 5% | > 10% | > 20% |
| 追溯闭合率 | Bidirectional_Traceable / Total | 100% | < 95% | < 90% |

阶段特有指标见 [`../../skills/testcase-generator/resources/quality_checklist.md#度量指标基线`](../../skills/testcase-generator/resources/quality_checklist.md)。

---

## 5. 质量报告模板

每次流水线完成时，必须产出符合以下结构的 `quality_report.md`：

```markdown
---
report_type: "quality_assurance_report"
generator: "testcase-generator v2.3.0"
project: "[Project Name]"
date: "{YYYY-MM-DD}"
overall_score: {N}/{100}
grade: "{A/B/C/D}"
verdict: "PASS / PASS_WITH_WARNINGS / FAIL"
---

# 质量检查报告

## 执行摘要

| 维度 | 得分 | 等级 | 状态 |
|------|------|------|------|
| Phase 0: 输入预处理 | N/100 | A-D | ✅ Pass / ⚠️ Warn / ❌ Fail |
| Phase 1: 需求分析 | N/100 | A-D | ✅ / ⚠️ / ❌ |
| Phase 2: 代码分析 | N/100 | A-D | ✅ / ⚠️ / ❌ |
| Phase 3: 领域建模 | N/100 | A-D | ✅ / ⚠️ / ❌ |
| Phase 4: MBT 设计 | N/100 | A-D | ✅ / ⚠️ / ❌ |
| Phase 5: 用例生成 | N/100 | A-D | ✅ / ⚠️ / ❌ |
| **综合得分** | **N/100** | **A-D** | **✅/⚠️/❌** |

## 各阶段详细评分

### Phase 1: [阶段名称]
| 检查组 | 权重 | 得分 | 加权分 | 状态 |
|-------|------|------|--------|------|
| [Group Name] | W% | S/100 | WS | ✅/⚠️/❌ |

#### 发现的问题
| 问题ID | 类型 | 检查项 | 严重性 | 描述 | 修复建议 | 状态 |
|-------|------|-------|-------|------|---------|------|
| Q-[NNN] | Error/Warning/Info | Gx-y | H/M/L | [desc] | [suggestion] | Open/Fixed/Ignored |

## 覆盖率总览
| 覆盖维度 | 目标 | 实际 | 差距 | 状态 |
|---------|------|------|------|------|
| 需求覆盖 | 100% | N% | ±N% | ✅/⚠️/❌ |
| ... | ... | ... | ... | ... |

## 改进建议
### 高优先级 (P0)
1. [建议]

### 中优先级 (P1)
1. [建议]

### 低优先级 (P2)
1. [建议]
```

---

## 6. 自动化执行

虽然门禁规则当前主要由 Skill 自身在阶段转换时口头执行，但有两条可自动化的路径：

| 路径 | 工具 | 适用阶段 |
|---|---|---|
| 静态审计 | `devtools/capability_audit.py` | 全阶段 — 检查产物文件存在、能力标记完整 |
| 内容质量审计 | `devtools/skill_quality_audit.py` | Phase 5 — 检查输出产物的字段完整性和评分阈值 |

更细粒度的自动评分（如"AC 二元化率"、"等价类重叠检查"）当前是**人工或 AI 自审**任务，尚未接入静态分析。

---

## 7. 评分争议处理

- **同分争议**：当两个检查项分数相同且互相冲突时，权重高的优先。
- **跨阶段不一致**：Phase N 的产物被 Phase N+1 推翻时，必须回到 Phase N 修复后再前进，不允许"先放行再回头补"。
- **外部审核**：Critical 系统的最终交付建议引入独立人工审核，签字确认后归档。
