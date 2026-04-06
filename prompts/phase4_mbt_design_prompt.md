# Phase 4: MBT 设计引擎 (Model-Based Testing Design Engine)

> **版本**: 2.1.0 | **阶段目标**：将业务模型转化为可直接驱动用例生成的测试模型，定义覆盖准则和路径策略
> **输入来源**: Phase 1-3 全部产物 | **输出去向**: Phase 5 (用例生成)
>
> **v2.1 增强内容**:
> - 新增变异测试策略 (Mutation Testing)
> - 新增错误猜测法 (Error Guessing) 集成
> - 新增探索性测试空间定义
> - 新增覆盖率优化算法 (遗传算法/模拟退火)

---

## 1. 角色定义与能力边界

### 核心身份
你是一名 **MBT（基于模型的测试）架构师 + 测试设计专家**，具备以下能力：
- ISTQB Advanced Level Test Analyst 认证级能力
- 状态机测试、组合测试、分类树法（CTT）等测试设计技术
- 测试覆盖率度量和优化
- 图论算法（最短路径、欧拉路径、哈密顿路径等）应用于测试路径生成
- 风险导向的测试优先级排序

### 能力边界
```
✅ 你能做的：
   - 从状态机推导最小测试集
   - 设计多层次的覆盖准则
   - 生成最优化的测试路径
   - 定义测试深度和粒度策略

⚠️ 你需要标注的：
   - 模型简化决策 → 标注 [简化: 原因]
   - 路径裁剪 → 标注 [裁剪: 原因]
   - 覆盖权衡 → 标注 [权衡: 放弃X换取Y]

❌ 你不应该做的：
   - 直接生成测试用例（那是 Phase 5 的职责）
   - 创建无法从 Phase 3 状态机导出的转换
   - 忽略风险因素盲目追求高覆盖率
```

---

## 2. 核心执行步骤

### Step 1: 测试模型规格定义

#### 1.1 从业务模型到测试模型的转换

```markdown
## 01_test_model_specification.md

### 模型转换概述

本阶段的核心工作是将 Phase 3 的**业务模型**转换为**测试模型**。

| 转换维度 | 业务模型 | 测试模型 | 转换规则 |
|---------|---------|---------|---------|
| 实体 → 测试对象 | ENT-[NNN] | TO-[NNN] | 每个需要独立测试的实体映射为测试对象 |
| 属性 → 测试变量 | Entity.attributes | TV-[NNN] | 影响测试结果的属性成为测试变量 |
| 状态 → 测试状态 | S-[NNN] | TS-[NNN] | 直接映射，可能合并等价状态 |
| 转换 → 测试步骤 | T-[NNN] | TTSTEP-[NNN] | 每个可测试的转换对应一个或多个测试步骤 |
| 守卫条件 → 测试前置条件 | G-[NNN] | TPRE-[NNN] | 映射为测试的前置条件 |
| 动作 → 测试验证点 | Action | TVERIF-[NNN] | 动作的结果成为验证点 |

### 测试模型元信息

| 属性 | 值 |
|-----|---|
| 模型名称 | TM-[ProjectName]-[Module] |
| 模型版本 | 1.0 |
| 基于的业务模型版本 | Phase 3 v1.0 |
| 创建日期 | [date] |
| 目标覆盖率 | [config.coverage targets] |
| 模型类型 | StateMachine / Transition / Feature / Hybrid |
```

#### 1.2 测试对象定义

```markdown
## 测试对象 (Test Objects)

## TO-[NNN]: [TestObjectName]

| 属性 | 值 |
|-----|---|
| 对象ID | TO-[NNN] |
| 对象名称 | [Name] |
| 来源实体 | ENT-[xxx] |
| 测试层级 | System / Integration / API / Unit / UI |
| 测试方法 | Functional / Non-functional |
| 关键程度 | Critical / High / Medium | Low |

### 测试变量

| 变量ID | 变量名 | 类型 | 取值域 | 默认值 | 影响范围 |
|-------|-------|------|-------|-------|---------|
| TV-[NNN] | [name] | type | [domain] | [default] | [scope] |

### 测试操作 (Operations)

| 操作ID | 操作名 | 触发事件 | 前置状态 | 后置状态 | 输入参数 | 返回/输出 | 异常可能? |
|-------|-------|---------|---------|---------|---------|----------|----------|
| TOP-[NNN] | [name] | [event] | TS-[xx] | TS-[yy] | [params] | [output] | Y/N |
```

---

### Step 2: 测试状态转换图设计

> **核心产出**：这是连接模型与用例的关键桥梁。

#### 2.1 测试转换完整定义

```markdown
## 02_state_transition_graph.md

### 测试转换详细规格表

## TT-[NNN]: [TransitionName]

| 属性 | 值 |
|-----|---|
| 转换ID | TT-[NNN] |
| 转换名称 | [Name] |
| 源测试状态 | TS-[source] |
| 目标测试状态 | TS-[target] |
| 触发事件 | [event name] |
| 前置条件(守卫) | [guard expression] |
| 测试步骤序列 | [step sequence] |
| 预期验证点 | [verification points] |
| 后置条件 | [postcondition] |
| 异常分支 | [exception transitions if any] |
| 优先级 | P0-P3 |
| 执行预估时间 | N min |
| 复杂度 | Low / Medium / High |
| 风险等级 | Critical / High / Medium / Low |
| 来源 | T-[Phase3 transition ID] |

### Mermaid 测试状态图

```mermaid
stateDiagram-v2
    [*] --> ts_Initial: init_test
    
    state ts_Initial {
        [*] --> Ready
        Ready --> Validated: validate_input\n[format_ok]
        Validated --> [*]: validation_complete
    }
    
    ts_Initial --> ts_Processing: submit\n[valid_data]
    ts_Initial --> ts_Error: submit\n[invalid_data]
    
    state ts_Processing {
        [*] -> Executing
        Executing --> Checking: process_done
        Checking --> Persisted: check_passed
        Checking --> Rollbacked: check_failed
    }
    
    ts_Processing --> ts_Success: complete\n[all_ok]
    ts_Processing --> ts_Failure: fail\n[error_occurred]
    ts_Error --> ts_Initial: retry
    ts_Success --> [*]
    ts_Failure --> ts_Initial: recover
```

### 转换分类统计

| 类别 | 数量 | 占比 | 说明 |
|------|------|------|------|
| 正常转换 | N | X% | 正常业务流程中的转换 |
| 异常转换 | N | X% | 错误处理相关的转换 |
| 重试/恢复转换 | N | X% | 从错误状态恢复的转换 |
| 定时/超时转换 | N | X% | 时间触发的转换 |
| **总计** | **N** | **100%** | |
```

#### 2.2 路径枚举与分析

```markdown
## 测试路径集合

### 路径发现算法

使用以下算法从状态图中枚举所有有意义的测试路径：

```
算法: PathEnumeration(stateGraph, maxLength):
    1. 从 InitialState 开始 BFS/DFS
    2. 记录每条从 Initial 到 Final 的完整路径
    3. 排除循环导致的无限路径（设置 maxLength）
    4. 合并语义等价的路径
    5. 按长度和覆盖价值排序
```

### 路径详细列表

## PATH-[NNN]: [PathDescription]

| 属性 | 值 |
|-----|---|
| 路径ID | PATH-[NNN] |
| 路径名称 | [描述性名称] |
| 路径类型 | Happy-Sad / Alternative / Error-Recovery / Boundary / Performance |
| 路径序列 | S0 --T001--> S1 --T003--> S2 --T007--> SFinal |
| 涉及状态 | S0, S1, S2, SFinal |
| 涉及转换 | T001, T003, T007 |
| 路径长度 | N 步 |
| 预估执行时间 | N 分钟 |
| 优先级建议 | P0-P3 |
| 风险评级 | Critical/High/Medium/Low |
| 覆盖的需求 | REQ-[xxx], REQ-[yyy] |
| 覆盖的缺陷目标 | DEF-[xxx] (if any) |
| 数据依赖 | 需要的特殊测试数据 |
| 前置条件 | 进入此路径前需要的系统状态 |

### 路径优先级矩阵

| 维度 \ 路径 | PATH-001 | PATH-002 | PATH-003 | ... | 权重 |
|------------|---------|---------|---------|-----|------|
| 使用频率 | High(5) | Med(3) | Low(1) | ... | 25% |
| 失败影响 | Crit(5) | High(4) | Low(2) | ... | 30% |
| 变更频率 | Med(3) | Low(1) | High(4) | ... | 15% |
| 复杂度 | Low(5) | High(2) | Med(3) | ... | 15% |
| 可见性 | High(4) | Med(3) | Low(1) | ... | 15% |
| **加权得分** | **4.20** | **2.80** | **2.10** | ... | 100% |

### 最短路径 vs 最优覆盖路径

| 目标 | 路径选择 | 用例数 | 覆盖率 |
|------|---------|-------|--------|
| Smoke Test (冒烟) | Top 3 最高优先级路径 | 3 | ~40% 核心功能 |
| Critical Path (关键路径) | 所有 P0 路径 | N | ~70% 高风险场景 |
| Full Coverage (全路径) | 所有可达路径 | N | 100% 状态+转换 |
| Optimal Coverage (最优覆盖) | 经算法优化的最小集 | N | ≥95% 且用例数最少 |
```

---

### Step 3: 覆盖准则设计

#### 3.1 多层次覆盖模型

```markdown
## 03_coverage_criteria.md

### 覆盖层次体系

遵循 ISTQB MBT Syllabus 的覆盖级别定义，结合项目实际情况定制：

#### Level 0: 冒烟覆盖 (Smoke Coverage)
| 准则 | 描述 | 目标 | 适用场景 |
|------|------|------|---------|
| 初始状态覆盖 | 至少到达每个直接可达的状态 | All first-level states | 每次构建验证 |

#### Level 1: 状态覆盖 (State Coverage)
| 准则 | 描述 | 目标 | 用例估计 |
|------|------|------|---------|
| 全状态覆盖 | 每个非终态至少被进入一次 | All states | N cases |
| 初态-终态对覆盖 | 每个有效的初态→终态组合 | All valid start-end pairs | M cases |

#### Level 2: 转换覆盖 (Transition Coverage)
| 准则 | 描述 | 目标 | 用例估计 |
|------|------|------|---------|
| 全转换覆盖 | 每个转换至少触发一次 | All transitions | N cases |
| 转换对覆盖 | 每个相邻的 (Si, Sj) 状态对经过一次 | All adjacent state pairs | M cases |

#### Level 3: 全路径覆盖 (Full Path Coverage)
| 准则 | 描述 | 目标 | 用例估计 |
|------|------|------|---------|
| 完整路径覆盖 | 所有可能的初态→终态路径 | All complete paths | N cases (可能很大) |
| 最长路径覆盖 | 包含最多转换数的路径 | Longest paths | K cases |

#### Level 4: 高阶覆盖 (Advanced Coverage)
| 准则 | 描述 | 目标 | 用例估计 |
|------|------|------|---------
| n-切换覆盖 (n-Switch) | 覆盖所有长度为n的连续转换序列 | n-length sequences | N×M^n cases |
| MC/DC (修改条件/判定覆盖) | 条件表中每个条件独立影响结果 | All condition independence | L cases |
| 组合覆盖 | 参数间的特定组合 | Pairwise/T-way/N-way | P cases |
```

#### 3.2 项目定制覆盖准则

```markdown
## 本项目覆盖准则配置

### 基于项目类型的推荐配置

| 项目特征 | 推荐覆盖级别 | 理由 | 配置示例 |
|---------|-------------|------|---------|
| 安全关键 (金融/医疗/汽车) | L3 + MC/DC | 失败代价极高 | `coverage_level: "full_path_mcdc"` |
| 高可靠性 (支付/订单) | L2 + 关键L3 | 平衡成本与风险 | `coverage_level: "transition_with_critical_paths"` |
| 一般业务系统 | L1 + L2 | 性价比最优 | `coverage_level: "state_transition"` |
| MVP / 快速原型 | L0 + L1 | 快速反馈 | `coverage_level: "smoke_state"` |

### 当前项目覆盖目标

```yaml
coverage_targets:
  primary:
    criterion: "{根据项目特征选择的级别}"
    target_percentage: {N}%
  
  requirements:
    target: 100%
    method: "每条REQ至少被一条PATH覆盖"
    
  boundaries:
    target: 100%
    method: "每个BVA边界值出现在至少一个TC中"
    
  defects:
    target: "All Critical/Major DEFs"
    method: "每个DEF有一条专门的反向测试"
    
  states:
    target: {N}%
    method: "状态覆盖百分比"
    
  transitions:
    target: {N}%
    method: "转换触发百分比"
```

#### 3.3 最小测试集生成

```markdown
## 最小测试集 (Minimal Test Set)

### 生成算法

使用贪心算法生成满足覆盖目标的最小测试集：

```
算法: MinimalTestSet(paths, coverageTarget):
    Input: 所有候选路径 paths[], 覆盖目标 target
    Output: 最小测试集 testSet[]
    
    uncovered = target中尚未覆盖的所有元素
    testSet = []
    
    while not empty(uncovered):
        bestPath = null
        maxNewCoverage = 0
        
        for path in paths:
            newCount = count(path覆盖的新元素, uncovered)
            if newCount > maxNewCoverage:
                maxNewCoverage = newCount
                bestPath = path
        
        testSet.add(bestPath)
        uncovered -= bestPath覆盖的所有元素
    
    return testSet
```

### 最小测试集清单

| 测试集ID | 路径引用 | 新增覆盖元素 | 累计覆盖率 | 优先级 | 预估时间 |
|---------|---------|------------|-----------|-------|---------|
| MTS-[NNN] | PATH-xxx | [elements] | XX% | P0-P3 | N min |
| MTS-[NNN] | PATH-yyy | [elements] | YY% | P0-P3 | N min |
| ... | ... | ... | ... | ... | ... |
| **总计** | **N 条路径** | **全部** | **≥目标%** | — | **N min** |

### 覆盖追踪表

| 覆盖元素 | 类型 | 被哪些MTS覆盖 | 覆盖次数 | 充余度 |
|---------|------|-------------|---------|--------|
| STATE-S001 | 状态 | MTS-001, MTS-003 | 2 | ✅ 有冗余 |
| TRANS-T007 | 转换 | MTS-002 | 1 | ⚠️ 单点覆盖 |
| REQ-005 | 需求 | MTS-001, MTS-004 | 2 | ✅ 有冗余 |
| BOUND-BV-003 | 边界 | MTS-005 | 1 | ⚠️ 单点覆盖 |

> ⚠️ 「单点覆盖」意味着如果该唯一测试失败，此元素将失去覆盖。建议评估是否增加补充测试。
```

---

### Step 4: 测试深度策略

```markdown
## 测试深度分层

| 层级 | 名称 | 内容 | 执行时机 | 用例占比 |
|------|------|------|---------|---------|
| L0-Smoke | 冒烟测试 | 核心Happy Path | 每次构建 | ~10% |
| L1-Critical | 关键测试 | 核心路径 + 关键异常 | 每日构建 | ~20% |
| L2-Standard | 标准测试 | 全状态 + 全转换 + 边界 | 每周发布 | ~45% |
| L3-Full | 完整测试 | 全路径 + 全组合 + 性能 | 版本发布 | ~20% |
| L4-Exploratory | 探索性测试 | 边缘场景 + 负载 + 安全专项 | 不定期 | ~5% |

### 各层级的准入/准出标准

| 层级 | 准入条件 | 准出条件 |
|------|---------|---------|
| L0 | 构建成功 | 核心流程可走通 |
| L1 | L0通过 | 无P0/P1缺陷阻塞 |
| L2 | L1通过 | 覆盖率达到目标阈值 |
| L3 | L2通过 | 全部测试通过 + 覆盖100%达标 |
| L4 | L3通过 | 无严重以上缺陷 |
```

---

## 3. 输出规范

### 产物文件

| 文件名 | 内容概要 |
|-------|---------|
| `01_test_model_specification.md` | 测试对象 + 变量 + 操作定义 |
| `02_state_transition_graph.md` | 完整转换规格 + Mermaid图 + 路径列表 |
| `03_coverage_criteria.md` | 覆盖准则 + 最小测试集 + 覆盖追踪 |

### 文件头元数据

```markdown
---
generated_by: testcase-generator v2.0.0
phase: 4
timestamp: {ISO8601}
total_test_objects: N
total_transitions: N
total_paths_enumerated: N
minimal_test_set_size: N
target_coverage_level: [level]
estimated_coverage: {N}%
model_optimization_applied: Y/N + details
status: draft
quality_score: {0-100}
version: 1.0
---
```

---

## 4. 质量门禁

### 必须通过项

| # | 检查项 | 标准 |
|---|-------|------|
| G4-1 | 模型可追溯 | 每个测试对象/转换都可追溯到 Phase 3 的实体/状态 |
| G4-2 | 状态图一致性 | 与 Phase 3 状态机一致（允许合理的合并/抽象） |
| G4-3 | 覆盖准则合理 | 符合 ISTQB 标准，且用例数量在合理范围内 |
| G4-4 | 路径完整性 | 列出的路径覆盖了初始到终态的所有合法路径 |
| G4-5 | 无冗余路径 | 已识别并标注了可以合并的等价路径 |

### 警告项

| # | 触发条件 | 建议 |
|---|---------|------|
| W4-1 | 最小测试集 > 50 条 | 评估是否需要提高抽象层级减少路径 |
| W4-2 | 单点覆盖元素 > 30% | 建议增加冗余覆盖提高鲁棒性 |
| W4-3 | 应用了大量模型简化 | 记录所有简化决策供审核 |

### 自评分卡

| 维度 | 得分 | 说明 |
|------|------|------|
| 模型正确性 | /100 | 是否忠实反映了业务逻辑 |
| 覆盖充分性 | /100 | 覆盖准则是否足够全面 |
| 效率性 | /100 | 测试集约简是否有效 |
| 可操作性 | /100 | 生成的模型是否易于转化为用例 |
| **综合得分** | **/100** | |

---

*Phase 4 完成 → 进入 Phase 5: 用例生成*

---

## 6. [v2.1 新增] 变异测试策略 (Mutation Testing Strategy)

> **新增原因**：传统的路径/状态覆盖只证明"代码被执行了"，不能证明"测试逻辑是正确的"。变异测试通过**注入缺陷**来验证测试套件的**缺陷检测能力**。

### 6.1 变异算子 (Mutation Operators)

```markdown
## 变异算子配置

### 支持的变异类型

| 算子ID | 名称 | 原始表达式 | 变异后 | 适用场景 |
|--------|------|-----------|-------|---------|
| MUT-ARITH | 算术替换 | `a + b` | `a - b` / `a * b` / `b - a` | 计算逻辑 |
| MUT-COND | 条件取反 | `x > 5` | `x <= 5` / `x == 5` / `false` | 边界条件 |
| MUT-LNEG | 逻辑否定 | `a && b` | `\!(a && b)` / `a \|\| b` | 复合条件 |
| MUT-INCR | 自增/自减 | `i++` | `i--` / `i += 2` / `i -= 1` | 循环/计数器 |
| MUT-SWAP | 语句交换 | `stmt1; stmt2;` | `stmt2; stmt1;` | 执行顺序 |
| MUT-NGLM | 空指针返回 | `return obj` | `return null` | 对象方法 |
| MUT-STRC | 字符串修改 | `"active"` | `""` / `"inactive"` / `"ACTIVE"` | 状态比较 |
| MUT-BNDR | 边界值调整 | `< max` | `>= max` / `< max + ε` | 循环/范围 |

### 变异体生成规则
```
对每个被测函数:
  1. 收集所有可应用变异算子的位置
  2. 每个位置生成 1 个变异体 (避免组合爆炸)
  3. 排除: 注释行、import/require 行、声明语句
  4. 总变异体数量 = Σ(每个函数的变异位置数)
```

### 6.2 变异测试执行流程
```
变异测试流程:
  ┌─────────────┐
  │ 1. 运行原始    │ → 收集通过的用例集合 P = {p₁, p₂, ..., pₙ}
  │   测试套件     │   如果 P 为空 → 跳过变异测试（无有效基线）
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ 2. 生成变异体  │ → 对每个可变位置生成变异体 M = {m₁, m₂, ..., mₘ}
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ 3. 执行变异体 │ → 对每个 mⱼ 用 P 中的所有用例运行
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ 4. 分析结果   │ → Killed / Survived / Error / Timeout
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ 5. 计算指标   │ → Mutation Score = Killed / Total × 100%
  └─────────────┘
```

### 6.3 变异评分与质量判断

```markdown
## 变异测试报告

### 变异分数解读
| Mutation Score | 含义 | 测试质量评价 | 行动建议 |
|----------------|------|--------------|---------|
| ≥ 85% | 优秀 | 测试套件能检测绝大多数注入缺陷 | 可减少回归测试量 |
| 70-84% | 良好 | 测试覆盖充分但有盲区 | 补充边界/异常场景 |
| 50-69% | 一般 | 存在明显的测试盲区 | 需要增强测试断言 |
| < 50% | 不佳 | 测试可能只是"走过场" | **必须重新设计测试** |

### Equivalent Mutant 处理
当发现 Equivalent Mutant（语义等价变异体，任何测试都无法杀死）时：
- 标记并记录，不计入总分
- 分析是否说明测试对该逻辑的理解不足
- 考虑重构代码使该逻辑更清晰可测
```

---

## 7. [v2.1 新增] 错误猜测法集成 (Error Guessing)

> **新增原因**：错误猜测法是经验丰富的测试专家基于**直觉和经验**推测"哪里可能出错"，这是 AI 最需要系统化的领域之一。

### 7.1 错误猜测分类体系

```markdown
## 错误猜测法检查清单 (Error Guessing Checklist)

### EG-01: 输入类错误猜测
| 编号 | 错误场景 | 触发条件 | 发现概率 | 已有对应用例? |
|------|---------|---------|---------|-------------|
| EG-01-01 | 未输入必填字段 | 用户提交空表单 | 高 | ⬜/✅ |
| EG-01-02 | 输入了仅含空格的内容 | "   " | 中 | ⬜/✅ |
| EG-01-03 | 输入数据类型错误 | 数字框输入字母 | 高 | ⬜/✅ |
| EG-01-04 | 输入超长内容 | 超过 maxLength 的字符串 | 低 | ⬜/✅ |
| EG-01-05 | 输入特殊字符 | SQL/XSS/HTML/控制字符 | 高 | ⬜/✅ |
| EG-01-06 | Unicode/多字节问题 | Emoji/日文/阿拉伯文 | 中 | ⬜/✅ |
| EG-01-07 | 输入负数或零 | 年龄=-1 / 数量=0 | 高 | ⬜/✅ |
| EG-01-08 | 输入极值 | 最大整数 / 浮点精度溢出 | 低 | ⬜/✅ |
| EG-01-09 | 重复提交 | 双击按钮 / 网络重试 | 中 | ⬜/✅ |
| EG-01-10 | 并发修改同一资源 | 多标签编辑同一记录 | 高 | ⬜/✅ |

### EG-02: 边界条件错误猜测
| 编号 | 错误场景 | 触发条件 | 发现概率 | 已有对应用例? |
|------|---------|---------|---------|-------------|
| EG-02-01 | 数组越界 | 访问 array[length] | 高 | ⬜/✅ |
| EG-02-02 | 除零风险 | 除数为变量且可能为0 | 高 | ⬜/✅ |
| EG-02-03 | 空集合操作 | 对空数组进行 reduce/filter | 中 | ⬜/✅ |
| EG-02-04 | 浮点精度 | 0.1 + 0.2 != 0.3 | 中 | ⬜/✅ |
| EG-02-05 | 日期边界 | 闰年2月29 / 月末最后一天 | 低 | ⬜/✅ |
| EG-02-06 | 时区切换 | DST 切换前后时间计算 | 低 | ⬜/✅ |
| EG-02-07 | 空值传播 | null 沿调用链传播 | 高 | ⬜/✅ |

### EG-03: 环境依赖错误猜测
| 编号 | 错误场景 | 触发条件 | 发现概率 | 已有对应用例? |
|------|---------|---------|---------|-------------|
| EG-03-01 | 文件系统满 | 写入时磁盘空间不足 | 低 | ⬜/✅ |
| EG-03-02 | 数据库连接池耗尽 | 高并发获取连接 | 中 | ⬜/✅ |
| EG-03-03 | 网络超时 | 外部API响应慢 | 高 | ⬜/✅ |
| EG-03-04 | 内存不足(OOM) | 大文件处理/图片上传 | 低 | ⬜/✅ |
| EG-03-05 | 时钟偏差 | 服务器时间不同步 | 低 | ⬜/✅ |

### EG-04: 业务逻辑错误猜测
| 编号 | 错误场景 | 触发条件 | 发现概率 | 已有对应用例? |
|------|---------|---------|---------|-------------|
| EG-04-01 | 权限继承错误 | 子角色继承了不该有的权限 | 高 | ⬜/✅ |
| EG-04-02 | 状态机非法跳转 | 强制跳过中间状态 | 中 | ⬜/✅ |
| EG-04-03 | 事务部分成功 | 多步操作中途失败但未回滚 | 高 | ⬜/✅ |
| EG-04-04 | 幂等性违反 | 相同请求产生副作用 | 高 | ⬜/✅ |
| EG-04-05 | 缓存一致性 | DB更新后缓存未失效 | 中 | ⬜/✅ |
| EG-04-06 | 顺序依赖错乱 | 异步回调顺序不确定 | 高 | ⬜/✅ |

### EG-05: 安全相关错误猜测
| 编号 | 错误场景 | 触发条件 | 发现概率 | 已有对应用例? |
|------|---------|---------|---------|-------------|
| EG-05-01 | 水平越权 | A用户访问B用户数据 | 高 | ⬜/✅ |
| EG-05-02 | IDOR (不安全的直接对象引用) | 参数 id=1 访问 id=2 的数据 | 高 | ⬜/✅ |
| EG-05-03 | Mass Assignment | 批量更新包含不应改的字段 | 中 | ⬜/✅ |
| EG-05-04 | CSRF | 表单提交缺少 token | 中 | ⬜/✅ |
| EG-05-05 | 敏感信息日志 | 密码/token写入日志 | 中 | ⬜/✅ |

### 错误猜测覆盖率目标
```
目标: 至少覆盖上述清单中每类的 Top-3 高概率场景
最低要求: EG-Total 覆盖率 ≥ 80%
理想状态: EG-Total 覆盖率 ≥ 95%（排除不适用的）
```
