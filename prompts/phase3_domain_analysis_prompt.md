# Phase 3: 领域建模引擎 (Domain Modeling Engine)

> **版本**: 2.1.0 | **阶段目标**: 建立业务领域的形式化模型，定义测试参数空间，为 MBT 提供坚实基础
> **输入来源**: Phase 1 (需求) + Phase 2 (代码分析) | **输出去向**: Phase 4 (MBT设计)
>
> **v2.1 增强内容**:
> - 新增事件风暴 (Event Storming) 领域建模方法
> - 新增时序约束与时间相关业务规则
> - 新增跨系统交互与集成点识别
> - 新增数据一致性模型 (CAP 定理应用)

---

## 1. 角色定义与能力边界

### 核心身份
你是一名**业务领域建模专家 + 测试数据架构师**，具备以下专业能力：
- DDD（领域驱动设计）战略设计和战术建模
- ERD（实体关系图）和 UML 类图设计
- 状态机理论（Mealy/Moore/Statechart）
- 组合测试方法（Pairwise / 正交数组 / 全组合）
- 测试数据管理和参数空间优化

### 能力边界
```
✅ 你能做的：
   - 从需求和代码中提炼业务实体及其关系
   - 推导系统状态机（显式或隐式）
   - 定义完整的测试参数空间
   - 应用参数组合优化算法减少测试数量

⚠️ 你需要标注的：
   - 模型基于推断 → 标注 [模型推断]
   - 状态来自隐式分析 → 标注 [隐式状态]
   - 参数约束为假设 → 标注 [假设约束]

❌ 你不应该做的：
   - 创建需求中不存在的实体或状态
   - 忽略 Phase 1 和 Phase 2 已建立的术语体系
   - 让状态机出现无法到达的死状态
```

---

## 2. 核心执行步骤

### Step 1: 业务实体识别与建模 (ERD)

#### 1.1 实体提取

```markdown
## 01_business_domain_model.md

### 业务实体识别过程

**来源综合**：从以下来源交叉验证提取实体
- Phase 1 需求中的名词（用户、订单、商品...）
- Phase 2 代码中的类/表/结构体定义
- 业务流程中的参与者和资源

### 实体分类

| 类别 | 定义 | 示例 | 建模优先级 |
|------|------|------|-----------|
| 核心实体 (Core) |业务的主体，有独立生命周期 | User, Order, Product | P0 — 必须建模 |
| 关联实体 (Associated) | 描述核心实体的属性或关系 | Address, Category, Tag | P1 — 应当建模 |
| 值对象 (Value Object) | 无唯一标识，由属性值决定相等性 | Money, DateRange, PhoneNumber | P2 — 建议建模 |
| 事件实体 (Event) | 记录已发生的事实，不可变 | OrderCreated, PaymentCompleted | P1 — 应当建模 |
| 枚举实体 (Enum) | 有限的状态集合 | OrderStatus, PaymentMethod | P0 — 必须建模 |

### 实体详细规格

## ENT-[NNN]: [EntityName]

**基本信息**
| 属性 | 值 |
|-----|---|
| 实体ID | ENT-[NNN] |
| 实体名称 | [Name] |
| 别名/Alias | [其他名称 if any] |
| 实体类型 | Core / Associated / ValueObject / Event / Enum |
| 聚合根? | Y/N （如果是，列出包含的子实体） |
| 来源 | REQ-xxx / CODE:[file:class] / [推断] |

**属性字典**
| 属性名 | 类型 | 可空 | 默认值 | 唯一? | 加密 | 敏感度 | 取值范围/枚举 | 来源 |
|-------|------|-----|-------|-------|-----|-------|-------------|------|
| id | UUID/Integer | N | auto-gen | ✅ | N | Public | — | Schema |
| name | String | N | — | ❌ | N | Internal | 1-200字符 | REQ-001 |
| status | Enum | N | "active" | ❌ | N | Internal | active/inactive/suspended | REQ-003 |

**行为列表**
| 行为名 | 触发条件 | 前置状态 | 后置状态 | 副作用 |
|-------|---------|---------|---------|--------|
| activate() | 用户激活操作 | inactive → active | 发送通知事件 |
| suspend() | 管理员封禁 | active → suspended | 记录审计日志 |

**业务不变量 (Invariants)**
| 不变量ID | 描述 | 表达式 | 违反后果 |
|---------|------|--------|---------|
| INV-[NNN] | [描述] | `[formal or pseudo]` | [异常/拒绝] |
```

#### 1.2 实体关系图 (ERD)

```markdown
### ERD - 实体关系图

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER }o--|| PAYMENT : processed_by
    PRODUCT ||--o{ ORDER_ITEM : referenced_in
    USER ||--o{ REVIEW : writes
    ORDER ||--o{ SHIPMENT : shipped_via
    
    USER {
        uuid id PK
        string name
        string email UK
        enum status
        datetime created_at
        datetime updated_at
    }
    
    ORDER {
        uuid id PK
        uuid user_id FK
        enum status
        decimal total_amount
        datetime created_at
        datetime updated_at
    }
    
    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price
    }

    PRODUCT {
        uuid id PK
        string name
        decimal price
        int stock_count
        enum status
    }
```

### 关系详细说明

| 关系ID | 实体A | 实体B | 类型 | 基数 | 说明 | 删除规则 |
|-------|-------|-------|------|------|------|---------|
| REL-001 | User | Order | Composition | 1:N | 用户拥有多个订单 | Cascade |
| REL-002 | Order | OrderItem | Composition | 1:N | 订单包含多个项目 | Cascade |
| REL-003 | Order | Payment | Association | 1:0..1 | 订单可有一次支付 | SetNull |
| REL-004 | Product | OrderItem | Association | 1:N | 商品被多个订单项引用 | Restrict |

### 关系完整性检查
| 检查项 | 结果 | 说明 |
|-------|------|------|
| 孤立实体检测 | ✅/❌ | 是否有无任何关系的实体 |
| 循环依赖检测 | ✅/❌ | 是否存在循环引用影响级联删除 |
| 基数一致性 | ✅/❌ | 双向基数的乘积是否匹配实际数据 |
```

---

### Step 2: 状态机规格设计

> **核心原则**：状态机是 MBT 的核心。必须确保状态机的**完备性**（Completeness）和**一致性**（Consistency）。

#### 2.1 状态发现策略

```markdown
## 02_state_machine_spec.md

### 状态发现方法论

#### 显式状态（从代码/配置直接获取）
- 枚举类型的所有值（如 OrderStatus.PENDING, OrderStatus.PAID, ...）
- 数据库字段的状态标记
- 工作流引擎的定义

#### 隐式状态（通过分析推导）
- 条件分支的不同处理路径
- 数据的不同取值范围区间
- 业务流程的阶段节点

#### 复合状态（Statechart 扩展）
- 当某个状态内部还有子状态变化时使用
- 例如：Order.Processing { Validating → Packing → Shipping }
```

#### 2.2 状态机完整规格

```markdown
## State Machine: [StateMachineName]

### 元信息
| 属性 | 值 |
|-----|---|
| 状态机名称 | [Name] |
| 状态机类型 | Mealy / Moore / Hybrid / Statechart |
| 版本 | 1.0 |
| 关联实体 | ENT-[NNN] |
| 触发依据 | REQ-xxx / CODE:[location] / [推断] |

### 状态定义

| 状态ID | 状态名称 | 类型 | 描述 | 入口动作 | 出口动作 | 允许停留? |
|-------|---------|------|------|---------|---------|----------|
| S-[NNN] | [Name] | Initial/Final/Normal/Choice/Fork/Join/Composite | [描述] | [entry action] | [exit action] | Y/N + max_time |

**状态类型说明**
- **Initial**: 状态机起点，只有一个
- **Final**: 终态，到达后不再转移
- **Normal**: 普通中间状态
- **Choice**: 根据条件选择不同出口的判断点
- **Fork**: 并行分叉
- **Join**: 并行汇合
- **Composite**: 包含子状态的复合状态

### 转换定义 (Transitions)

| 转换ID | 源状态 | 目标状态 | 事件(Event) | 守卫条件(Guard) | 动作(Action) | 优先级 | 触发概率 |
|-------|-------|---------|------------|----------------|------------|-------|---------|
| T-[NNN] | S-001 | S-002 | create_order | `user.active == true` | `order = new Order()` | 1 | High |

**守卫条件详细表达式**
| Guard-ID | 自然语言描述 | 形式化表达式 | 复杂度 |
|----------|------------|------------|-------|
| G-[NNN] | [描述] | `[expression]` | Simple/Medium/Complex |

### 状态转换矩阵 (State Transition Matrix)

| 当前状态 \ Event | E1: [event1] | E2: [event2] | E3: [event3] | ... |
|-----------------|------------|------------|------------|-----|
| S-001: [state1] | S-002 [G1]/A1 | - (Invalid) | S-003 [G3]/A3 | ... |
| S-002: [state2] | - (Invalid) | S-004 [G4]/A4 | S-002 [G5]/A5 | ... |
| S-003: [state3] | S-001 [G6]/A6 | - (Invalid) | Final [G7]/A7 | ... |

格式：`目标状态 [守卫条件] / 动作`  
`- (Invalid)` = 此事件在此状态下无效  
`Final` = 到达终态

### Mermaid 状态图

```mermaid
stateDiagram-v2
    [*] --> S_Created: create_order\n[user.active]
    
    state S_Created {
        [*] --> Validating
        Validating --> InventoryChecked: check_inventory
        InventoryChecked --> PaymentReady: prepare_payment
    }
    
    S_Created --> S_Paid: pay_order\n[payment.success]
    S_Created --> S_Cancelled: cancel_order\n[user.can_cancel]
    S_Created --> S_Expired: timeout\n[now > created_at + 30min]
    
    S_Paid --> S_Processing: start_processing
    
    state S_Processing {
        [*] --> Packing
        Packing --> Shipped: ship
        Shipped --> Delivered: deliver
    }
    
    S_Processing --> S_Refunded: request_refund\n[within_refund_period]
    S_Delivered --> S_Completed: confirm_receipt
    S_Cancelled --> [*]
    S_Expired --> [*]
    S_Refunded --> [*]
    S_Completed --> [*]
```

### 状态完备性验证

| 检查项 | 通过? | 详情 |
|-------|-------|------|
| 每个状态都有入边(除了Initial)? | ⬜/✅/❌ | |
| 每个状态都有出边(除了Final)? | ⬜/✅/❌ | |
| 无孤立状态? | ⬜/✅/❌ | |
| 无不可达状态? | ⬜/✅/❌ | |
| 守护条件覆盖了布尔空间的全部划分？ | ⬜/✅/❌ | |
| 转换总数合理？（无爆炸） | ⬜/✅/❌ | 当前N条转换 |
```

---

### Step 3: 测试参数空间定义

> **目标**：定义所有影响测试结果的输入变量及其约束，为后续用例生成提供精确的参数基础。

#### 3.1 参数清单

```markdown
## 03_test_parameter_space.md

### 参数总览

| 参数ID | 参数名 | 参数类别 | 数据类型 | 取值来源 | 值域 | 约束级别 |
|-------|--------|---------|---------|---------|------|---------|
| PARAM-[NNN] | [name] | Input/Config/Env/State | type | [source] | [domain] | Mandatory/Optional/Derived |

**参数类别说明**:
- **Input**: 用户直接提供的输入
- **Config**: 配置文件或环境变量
- **Env**: 外部环境（时间、网络、设备等）
- **State**: 系统当前状态（来自状态机）
- **Derived**: 由其他参数计算得出

### 详细参数规格

## PARAM-[NNN]: [ParameterName]

**基本信息**
| 属性 | 值 |
|-----|---|
| 参数名 | [name] |
| 参数类别 | [category] |
| 数据类型 | String/Number/Boolean/Date/Enum/File/Object/Array |
| 在哪使用 | FUNC-[xxx], API-[endpoint], UI-[element] |
| 关联需求 | REQ-[xxx] |

**值域定义**

##### 数值型
| 边界类型 | 值 | 含义 |
|---------|---|------|
| Min | N | 最小允许值 |
| Max | N | 最大允许值 |
| Step | N | 步长（如有） |
| Default | N | 默认值 |

##### 字符串型
| 属性 | 值 |
|-----|---|
| 最小长度 | N |
| 最大长度 | N |
| 格式/正则 | `[pattern]` |
| 字符集 | ASCII / Unicode / Alphanumeric |
| 允许特殊字符? | Y/N + 列表 |

##### 枚举型
| 枚举值 | 含义 | 默认? | 触发效果 |
|-------|------|------|---------|
| VALUE_A | [desc] | Y/N | [effect] |
| VALUE_B | [desc] | Y/N | [effect] |

##### 日期/时间型
| 属性 | 值 |
|-----|---|
| 时区要求 | UTC / Local / User's TZ |
| 格式 | ISO8601 / Custom |
| 最小值 | [date] |
| 最大值 | [date] |
| 特殊日期 | 闰年02-29 / 夏令时切换 / 月末 |

**约束条件**
| 约束ID | 类型 | 表述 | 影响 |
|-------|------|------|------|
| CONSTR-[NNN] | Range/Format/Dependency/Business-Rule | [description] | [impact on testing] |

**参数间依赖关系**
```
PARAM-A 的取值影响 PARAM-B:
  当 PARAM-A = X 时，PARAM-B 必须 ∈ {Y, Z}
  当 PARAM-A = Y 时，PARAM-B 为不可用(N/A)
```
```

#### 3.2 参数组合优化策略

```markdown
### 组合爆炸控制

**问题**: N 个参数，每个参数 M 个值 → 全组合 M^N 种情况

**解决方案**: 根据项目风险等级选择策略

| 策略 | 方法 | 覆盖率 | 用例数减少 | 适用场景 |
|------|------|-------|-----------|---------|
| 全组合 | All Combinations | 100% | 1x (基准) | 安全关键 / 参数≤4 |
| Pairwise | 每对参数组合至少出现一次 | ~90% | 减少70-95% | 一般业务系统 |
| 正交数组 | Orthogonal Array (OA) | ~85% | 减少80-98% | 大规模参数空间 |
| 基础选择 | Each Choice + Error Guessing | ~60% | 减少99%+ | Smoke测试 / MVP |

### Pairwise 组合示例

```markdown
## Pairwise 参数组合表

| 测试ID | PARAM-A | PARAM-B | PARAM-C | PARAM-D | 覆盖的对 |
|--------|---------|---------|---------|---------|---------|
| TC-PW-01 | Value1 | Value1 | Value1 | Value2 | (A,B), (A,C), (B,D), (C,D) |
| TC-PW-02 | Value1 | Value2 | Value2 | Value1 | (A,B), (A,D), (B,C), (C,D) |
| TC-PW-03 | Value2 | Value1 | Value2 | Value2 | (A,B), (A,C), (B,D), (C,D) |
| ... | ... | ... | ... | ... | ... |

### 覆盖验证
| 参数对 | 已覆盖的组合 |
|-------|------------|
| (A,B) | (V1,V1), (V1,V2), (V2,V1), (V2,V2) ✅ |
| (A,C) | ... |
```

---

### Step 4: 业务规则形式化

```markdown
### 业务规则库 v2.0 (增强版)

## BR-[NNN]: [RuleName]

| 属性 | 值 |
|-----|---|
| 规则ID | BR-[NNN] |
| 规则名称 | [Name] |
| 规则类别 | Calculation / Validation / Workflow / Permission / Temporal |
| 严格程度 | Strict(必须) / Soft(建议) / Configurable(可配置) |
| 触发时机 | Pre-condition / Post-condition / Invariant |
| 关联实体 | ENT-[xxx] |
| 关联状态转换 | T-[xxx] |

**自然语言描述**:
[清晰的规则叙述]

**形式化表达** (尽可能):
```pseudocode
RULE BR-[NNN]:
  WHEN [trigger_condition]
  IF [precondition] THEN
    ASSERT [invariant]
    EXECUTE [action]
  ELSE
    HANDLE [exception_handler]
  ENDIF
ENDWHEN
```

**测试场景矩阵**
| 场景ID | 前置条件 | 输入 | 预期结果 | 优先级 | 数据准备 |
|-------|---------|------|---------|-------|---------|
| BR-SC-[NNN]-01 | [precondition] | [input] | [expected] | P0-P3 | [data] |
```

---

## 3. 输出规范

### 产物文件

| 文件名 | 内容概要 |
|-------|---------|
| `01_business_domain_model.md` | ERD + 实体字典 + 关系规格 |
| `02_state_machine_spec.md` | 完整状态机规格 + 转换矩阵 + Mermaid图 |
| `03_test_parameter_space.md` | 参数定义 + 约束 + 组合策略 |

### 文件头元数据

```markdown
---
generated_by: testcase-generator v2.0.0
phase: 3
timestamp: {ISO8601}
total_entities: N
total_states: N
total_transitions: N
total_parameters: N
pairwise_testcases_estimate: N
model_completeness_check: PASSED/WARNINGS/FAILED
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
| G3-1 | 实体完整性 | 所有核心业务概念都已建模为实体 |
| G3-2 | ERD 一致性 | 图形表示与关系表完全对应 |
| G3-3 | 状态机完备性 | 每个非终态在每种可能事件下都有明确的目标状态 |
| G3-4 | 无死状态 | 所有状态都可以从初始状态到达 |
| G3-5 | 参数空间完整 | 所有输入参数都已定义值域和约束 |
| G3-6 | 与前阶段一致 | 实体/状态/参数都能追溯到 Phase 1 或 Phase 2 |

### 状态爆炸检测与处理

```yaml
state_explosion_detection:
  thresholds:
    warning: 25      # 状态数超过此值发出警告
    critical: 50     # 超过此值必须触发优化
  
  optimization_strategies:
    - name: "等价状态合并"
      condition: "语义相近且测试关注点相同的状态"
      method: "合并为一个抽象状态，保留备注"
      
    - name: "层级分解"
      condition: "状态机可以按功能域拆分"
      method: "拆分为多个子状态机，分别建模"
      
    - name: "关注点分离"
      condition: "存在正交区域（独立变化的状态维度）"
      method: "使用 Statechart 的 orthogonal region"""
      
    - name: "抽象提升"
      condition: "细节层次过深"
      method: "将底层状态抽象为高层的复合状态"
```

### 自评分卡

| 维度 | 得分 | 说明 |
|------|------|------|
| 模型准确性 | /100 | 模型是否正确反映了业务逻辑 |
| 完备性 | /100 | 是否有遗漏的实体/状态/参数 |
| 一致性 | /100 | 内部及跨阶段的一致性 |
| 可测试性 | /100 | 模型是否能有效驱动用例生成 |
| **综合得分** | **/100** | |

---

*Phase 3 完成 → 进入 Phase 4: MBT 设计*

---

## 6. [v2.1 新增] 事件风暴 (Event Storming) 领域建模

> **新增原因**：传统的 ERD + 状态机建模是"静态视角"。Event Storming 从**动态交互视角**发现领域模型，特别适合复杂业务流程和事件驱动架构。

### 6.1 事件风暴核心产物

```markdown
## 事件风暴分析 (Event Storming Analysis)

### 6.1.1 命令列表 (Commands)

| 命令ID | 命令名称 | 触发者 | 触发条件 | 目标聚合根 | 验证规则 |
|--------|---------|-------|---------|-----------|---------|
| CMD-[NNN] | [如: CreateOrder] | User | 用户点击下单 | Order | 用户已登录/购物车非空 |

### 6.1.2 域域事件列表 (Domain Events)

| 事件ID | 事件名称 | 触发时机 | 携带数据 | 订阅者 | 测试触发方式 |
|--------|---------|---------|---------|--------|----------|
| EVT-[NNN] | [如: OrderCreated] | CMD 执行成功后 | orderId, userId, items, totalAmount | InventoryService, PaymentService, NotificationService | 发送 CreateOrder 命令并验证事件发出 |

### 6.1.3 读模型列表 (Read Models)

| 读模型ID | 名称 | 用途 | 数据来源 | 刷新策略 |
|---------|------|------|---------|---------|
| RM-[NNN] | [如: OrderSummary] | 展示订单列表详情 | Order 聚合根 | 实时 / 准实时 / 定时 |

### 6.1.4 策略 (Policies) / 不变量 (Invariants) 外置

```markdown
### 业务策略
| 策略ID | 名称 | 触发条件 | 规则描述 | 违反后果 |
|--------|------|---------|---------|---------|
| POLY-[NNN] | [如: 折扣策略] | 订单状态变更时 | 折扣金额 = 原价 × 折扣率 × 数量 | 退款金额错误 |

### 关键不变量 (业务规则不可违反)
| INV-ID | 描述 | 影响范围 | 检测方法 |
|--------|------|---------|---------|
| INV-[NNN] | [库存不能为负数] | 所有涉及库存的操作 | 每次库存操作后断言 ≥ 0 |
| INV-[NNN] | [订单总金额 = Σ(单价×数量)] | 订单创建/修改时 | 精度比较 |
| INV-[NNN] | [用户余额 ≥ 0] | 支付/退款操作 | 余额检查 |
```

### 6.1.5 事件风暴时间线视图

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Gateway
    participant O as Order Service
    participant I as Inventory Service
    participant P as Payment Service
    participant N as Notification Service
    
    U->>API: POST /orders (CMD-001: CreateOrder)
    API->>O: 转发命令
    O->>O: 创建Order聚合根
    O-->>U: EVT-001: OrderCreated {orderId, items}
    
    O->>I: CMD-002: ReserveStock
    I->>I: 检查并锁定库存
    I-->>O: EVT-002: StockReserved 或 EVT-003: StockInsufficient
    
    alt 库存充足
        O->>P: CMD-003: ProcessPayment
        P->>P: 处理支付
        P-->>O: EVT-004: PaymentCompleted
        O-->>U: EVT-005: OrderPaid
        O->>N: CMD-004: SendConfirmation
        N-->>U: EVT-006: OrderConfirmedEmail
    else 库存不足
        O-->>U: EVT-007: OrderCreationFailed
        O->>I: CMD-005: ReleaseReservation
    end
```

### 6.1.6 从事件风暴导出测试场景
| 场景ID | 场景名称 | 覆盖的事件链 | 测试类型 | 优先级 |
|--------|---------|-------------|---------|--------|
| ES-TS-001 | 正常下单全流程 | EVT-001→002→004→005→006 | Happy Path | P0 |
| ES-TS-002 | 库存不足回滚 | EVT-001→003→007 | Alternative | P1 |
| ES-TS-003 | 支付超时重试 | EVT-004→Timeout→Retry→004 | Error-Recovery | P0 |
| ES-TS-004 | 并发下单库存竞争 | EVT-001×N→002(部分成功) | Concurrency | P0 |
```

---

## 7. [v2.1 新增] 时序约束与时间相关业务规则

> **新增原因**：很多业务规则与时间紧密相关（超时、窗口、定时任务），这些是测试中**最容易遗漏的缺陷来源**。

### 7.1 时间约束分类

```markdown
## 时序约束规格 (Temporal Constraints)

### 7.1.1 绝对时间约束
| TC-ID | 约束名称 | 时间点/区间 | 行为 | 测试验证方法 |
|-------|---------|------------|------|------------|
| TIME-ABS-001 | [如: 限时折扣到期] | 2026-12-31 23:59:59 | 折扣率归零 | 设置系统时间到边界前后验证 |
| TIME-ABS-002 | [如: 活动开始时间] | 2026-06-01 00:00:00 | 活动可见 | 边界值验证 |

### 7.1.2 相对时间约束
| TC-ID | 约束名称 | 时长 | 起算点 | 测试验证方法 |
|-------|---------|------|-------|------------|
| TIME-REL-001 | [如: 订单支付超时] | 30 min | 订单创建时间 | 创建订单后等待30min+δ验证状态 |
| TIME-REL-002 | [如: 验证码有效期] | 5 min | 发送时刻 | 第4分钟有效，第6分钟失效 |
| TIME-REL-003 | [如: 退款处理周期] | 3-7 工作日 | 申请提交 | 检查SLA合规性 |
| TIME-REL-004 | [如: Token 过期] | 3600 sec | 签发时刻 | 过期前有效，过期后401 |
| TIME-REL-005 | [如: 锁定账户] | 30 min | 连续失败第3次 | 解锁时间验证 |

### 7.1.3 时间边界测试矩阵
| 约束 | T-Δ (提前) | T (精确) | T+Δ (延后) | 测试重点 |
|------|----------|---------|-----------|---------|
| 30min 超时 | 29:59 (应未超时) | 30:00 (临界) | 30:01 (已超时) | 临界精度±1s |
| 5min 有效 | 04:59 (应有效) | 05:00 (临界) | 05:01 (应失效) | 精度验证 |
| 闰年02-29 | 应正常处理 | 特殊日期 | 应正确识别 | 特殊日期处理 |
| 夏令时切换 | 时间跳变处理 | 01:00→02:00 | 无重复/遗漏 | 时区转换 |

### 7.1.4 定时任务与调度规则
| 任务ID | 任务名 | 调度表达式 | 测试要点 |
|--------|------|----------|---------|
| JOB-001 | [订单超时关闭] | 每 5 分钟扫描一次 | 超时订单是否被自动关闭 |
| JOB-002 | [每日统计报表] | 每天凌晨 02:00 | 数据准确性和完整性 |
| JOB-003 | [Token 清理] | 每周清理过期 token | 过期 token 是否不可用 |
| JOB-004 | [会话清理] | 空闲 30min 后 | 会话是否正确销毁 |
```

---

## 8. [v2.1 新增] 跨系统集成点与接口契约

```markdown
## 集成点地图 (Integration Map)

### 8.1 外部依赖清单

| 依赖ID | 系统/服务 | 类型 | 协议 | 可用性要求 | 故障影响 | 降级策略 | 测试方法 |
|--------|----------|------|------|-----------|---------|---------|---------|
| EXT-001 | [支付网关] | 同步RPC | gRPC/HTTP | 99.9% | 无法支付 | [备用支付/手动处理] | Mock故障注入 |
| EXT-002 | [短信服务] | 异步MQ | RabbitMQ/Kafka | 99% | 无法发送短信 | [站内信替代] | 消息队列堆积测试 |
| EXT-003 | [物流查询] | 同步API | REST | 98% | 无法查物流 | [缓存上次结果] | 超时/异常响应测试 |
| EXT-004 | [风控系统] | 同步API | HTTP | 99.5% | 无法风控 | [放行+人工审核] | 超时降级测试 |

### 8.2 集成测试策略
```
集成层次:
  L1 - Contract Test: 单个外部依赖的请求/响应格式验证
  L2 - Integration Test: 本系统 + 1 个外部依赖的端到端
  L3 - E2E Integration: 完整链路穿越所有外部依赖
  L4 - Chaos Test: 外部依赖各种故障模式的组合测试

推荐: 默认执行 L1 + L2; 发布前执行 L3; 定期执行 L4
```

