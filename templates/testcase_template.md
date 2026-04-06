# 测试用例模板 v2.0 (生产级)

> **模板版本**: 2.0.0 | **标准**: IEEE 829 + ISTQB + Agile hybrid | **用途**: Phase 5 用例生成输出

---

```markdown
---
document_type: "testcase"
template_version: "2.0.0"
generated_by: "testcase-generator v2.0.0"
metadata:
  testcase_id: "TC-[PHASE]-[MOD]-[NNN]"
  version: "1.0"
  status: "Draft"  # Draft / Reviewed / Approved / Deprecated / Obsolete
  created: "{YYYY-MM-DDTHH:mm:ssZ}"
  last_modified: "{YYYY-MM-DDTHH:mm:ssZ}"
  author: "AI Generator v2.0"
  reviewer: ""
  approver: ""
  automation:
    ready: "Yes|Partial|No|N/A"
    framework_recommendation: "[Pytest/JUnit/Playwright/Cucumber/Postman/etc]"
    implementation_status: "Not-Started|In-Progress|Completed|Skipped"
  priority: "P0|P1|P2|P3"
  execution:
    estimated_duration_minutes: N
    actual_duration_minutes: null
    last_execution_date: null
    last_execution_result: null
    total_executions: 0
    pass_rate: null
traceability:
  requirements: ["REQ-xxx"]
  paths: ["PATH-xxx"]
  transitions: ["TT-xxx"]
  states: ["S-xxx"]
  defects: ["DEF-xxx"]  # 如果是反向/回归测试
change_history:
  - version: "1.0"
    date: "{date}"
    author: "AI Generator v2.0"
    change: "Initial creation from Phase 4 test model"
---

# TC-[PHASE]-[MOD]-[NNN]: [测试用例标题]

## 1. 基本信息卡

### 1.1 核心属性

| 属性 | 值 |
|-----|---|
| **用例ID** | TC-[PHASE]-[MOD]-[NNN] |
| **用例标题** | [清晰、唯一、可理解的标题，格式：验证[对象]在[条件]下的[预期行为]] |
| **测试类型** | `□` Functional `□` API `□` UI `□` E2E `□` Security `□` Performance `□` Compatibility `□` Accessibility |
| **测试子类型** | Happy-Path / Boundary / Error-Recovery / Alternative / Negative / Conformance / Smoke / Regression |
| **优先级** | 🔴 **P0** (阻塞) / 🟠 P1 (严重) / 🟡 P2 (一般) / 🔵 P3 (低优先级) |
| **所属模块** | [Module / Feature Name] |
| **所属套件** | TS-[SuiteName] |
| **复杂度** | ⭐ Simple (≤3步) / ⭐⭐ Medium (4-7步) / ⭐⭐⭐ Complex (8-15步) / ⭐⭐⭐⭐ Very Complex (>15步) |

### 1.2 分类标签

```
Tags: [module-name], [feature], [priority-P0], [type-functional], 
      [smoke], [regression], [api], [security], [positive/negative]
```

### 1.3 联系与负责人

| 角色 | 姓名/团队 | 联系方式 |
|------|---------|---------|
| 用例设计者 | AI Generator v2.0 | — |
| 用例审核人 | [待分配] | — |
| 自动化实现者 | [待分配] | — |
| 测试执行者 | [待分配] | — |

---

## 2. 需求追溯

### 2.1 正向追溯（本用例覆盖了什么）

| 追溯类型 | ID | 描述 | 覆盖方式 | 验证方法 |
|---------|-----|------|---------|---------|
| **需求** | REQ-[xxx] | [需求摘要] | Direct / Indirect / Implicit | [如何在此用例中验证] |
| **路径** | PATH-[xxx] | [路径描述] | Full / Partial (N%) | [覆盖的步骤范围] |
| **转换** | TT-[xxx] | [转换名称] | Complete / Trigger-only | [触发的具体转换] |
| **状态** | S-[xxx] | [状态名] | Entry / Exit / Both | [进入/离开的验证] |
| **缺陷目标** | DEF-[xxx] | [缺陷描述] | Reproduction / Verification | [复现或验证的方式] |

### 2.2 独占贡献（本用例独有的覆盖价值）

> 列出只有**这个用例**才能覆盖到的内容。如果删除此用例，以下内容将失去覆盖：

- [独占覆盖点 1]
- [独占覆盖点 2]

### 2.3 反向追溯（如果移除此用例的影响）

| 影响维度 | 当前覆盖情况 | 移除后 | 风险评估 |
|---------|------------|--------|---------|
| REQ-[xxx] 覆盖 | 由 TC-A, TC-B, **TC-本用例** 覆盖 | 仍被 TC-A, TC-B 覆盖 | 🟢 低风险 |
| PATH-[yyy] 覆盖 | **仅由本用例** 覆盖 | ❌ 将失去覆盖 | 🔴 高风险 |

---

## 3. 前置条件 (Preconditions)

### 3.1 系统状态

```
✅ 系统必须处于以下状态：
   · 当前实体状态: TS-[state_id] ([state_name])
   · 相关实体的必要状态: [列出所有相关状态]
   · 全局配置: [config items and values]
   
❌ 系统不得处于以下状态：
   · [forbidden state 1]
   · [forbidden state 2]
```

### 3.2 测试数据准备

#### 必需数据

| 数据ID | 数据描述 | 类型 | 准备方式 | 数量 | 来源 |
|-------|---------|------|---------|------|------|
| DATA-[NNN] | [description] | Master/Transaction/Reference/Config | SQL/API/UI/Seed | N | Pre-created/Dynamic/Fixture |

**详细数据规格**:

```yaml
DATA-[NNN]: # 示例：用户数据
  entity: User
  attributes:
    id: "auto-generated"
    username: "[specific value or pattern]"
    email: "[value]"
    password: "[hashed or plain for testing]"
    status: "active"  # 必须是 active
    role: "regular_user"
    created_at: "{{ now }} registration_data:
      method: "email_verification"
      verified: true
    preferences:
      language: "zh-CN"
      timezone: "Asia/Shanghai"
  
  uniqueness_constraints:
    - username  # 必须全局唯一
    - email     # 必须全局唯一
  
  cleanup_strategy: "delete_after_test" # or "soft_delete" or "keep_for_audit"
```

#### 可选数据

| 数据ID | 描述 | 是否必需 | 默认值 |
|-------|------|---------|--------|

### 3.3 环境配置

| 维度 | 要求 | 验证命令/方法 |
|------|------|-------------|
| 浏览器 | Chrome ≥ 120 / Firefox ≥ 120 | `--version` |
| API 环境 | Staging (`https://api-staging.example.com`) | `curl https://api-staging.example.com/health` |
| 数据库 | 测试数据库 (test_db) | `SELECT count(*) FROM information_schema.tables` |
| 服务依赖 | Redis, Elasticsearch, Kafka 均可用 | Health check endpoints |
| 网络条件 | 延迟 < 100ms, 丢包 < 0.1% | `ping target_host` |

### 3.4 权限与认证

| 项目 | 值 |
|-----|---|
| 测试账号类型 | [admin/test-user/guest/api-key] |
| 认证方式 | [JWT Session / OAuth2 / API Key / Basic Auth] |
| Token/Session | [获取方式或固定值] |
| 权限角色 | [role name] |
| IP 白名单? | Yes (需要添加测试IP) / No |

### 3.5 时间窗口约束

| 约束类型 | 说明 | 处理方式 |
|---------|------|---------|
| 业务时间窗口 | 如：仅在工作日 9:00-18:00 可操作 | 使用 Mock 时间 或调整测试时间 |
| 缓存有效期 | 如：验证码 5 分钟有效 | 在有效期内完成测试 |
| 数据新鲜度 | 如：价格信息每 10 分钟更新 | 确保数据未过期 |

---

## 4. 测试数据 (Test Data)

### 4.1 输入数据表

| 参数# | 参数名 | 参数类型 | 测试值 | 格式要求 | 编码方式 | 敏感度 | 来源 | 备注 |
|-------|-------|---------|--------|---------|---------|-------|------|------|
| 1 | [param_name] | String/Number/Boolean/Date/Enum/File/Object/Array | `[value]` | `[format]` | UTF-8/Base64/URL/Multipart | Public/Internal/Confidential/Restricted | EQ/BV/Custom | [note] |

### 4.2 边界值标记

对每个涉及边界的参数，明确标注：

```
param_1 = 100     ← Nominal Value (正常值)
                    ↓
边界分析:
  min-1: 99        ← 下边界内
  min:   100       ← 最小边界 ✅ 本用例使用
  min+1: 101       ← 上边界内
  max:   10000     ← 最大边界
  max+1: 10001     ← 超上边界 → 参考用例 TC-XXX-002
```

### 4.3 特殊值说明

| 参数 | 特殊值类型 | 值 | 目的 | 预期处理 |
|------|-----------|---|------|---------|
| param_x | Null/Empty | `null` / `""` | 测试空值处理 | 拒绝/使用默认值 |
| param_y | SQL Injection | `'; DROP TABLE; --` | 安全性测试 | 应被转义/拒绝 |
| param_z | Unicode | `中文🎉é` | 多语言支持 | 正确处理 |
| param_w | 超长字符串 | `{2000 chars}` | 最大长度边界 | 截断/拒绝 |

---

## 5. 执行步骤 (Test Steps)

### 5.1 步骤表

| 步骤# | 操作类别 | 操作描述 | 操作对象 | 详细操作 | 输入数据 | 预期结果 | 验证方式 | 截图? | 日志级别 |
|-------|---------|---------|---------|---------|---------|---------|---------|-------|---------|
| 1 | Navigate | 打开页面 | Browser | `open(url)` | URL: `[url]` | 页面加载成功 | Visual Check | ⬜ | INFO |
| 2 | Input | 输入字段 | Element `#username` | `type(text)` | `[value]` | 字段显示输入值 | Visual + Assert | ⬜ | DEBUG |
| 3 | Click | 点击按钮 | Element `#submit-btn` | `click()` | — | 触发提交请求 | Network Assert | ✅ | INFO |
| 4 | Verify | 验证响应 | API Response | `assert(response)` | — | 返回 code=200 | JSON Schema | ⬜ | INFO |
| 5 | Verify | 验证UI变化 | Page | `expect(element)` | — | 显示成功提示 | DOM Assert | ✅ | INFO |

### 5.2 步骤详细说明

针对复杂步骤的展开：

```
═════════════════════════════════════════════════════════
Step 3: 点击提交按钮并等待响应
═════════════════════════════════════════════════════════

操作详情:
  · 定位方式: CSS Selector `#submit-button.form-primary`
  · 操作类型: click() with { force: true }
  · 等待条件: 
    - 按钮 disabled 属性变为 true (表示提交中)
    - loading spinner 出现
    - 或 network request 发出

预期中间态 (Immediate Feedback):
  ┌─────────────────────┐
  │ 🔄 提交中...请稍候   │  ← 按钮变为禁用 + spinner
  └─────────────────────┘

预期终态 (Final State):
  ┌─────────────────────┐
  │ ✅ 提交成功！         │  ← 成功提示出现
  │ 订单号: ORD-20240404 │  ← 显示关键信息
  └─────────────────────┘

验证点清单:
  ☐ HTTP POST /api/orders 返回 201 Created
  ☐ Response body 包含 order_id (非null UUID)
  ☐ 成功消息文本包含 "成功"
  ☐ 按钮恢复为可点击状态
  ☐ 页面 URL 变更为 /orders/{order_id}
  ☐ 数据库 orders 表新增一条记录

异常分支 (如果在 Step 3 出现问题):
  ├─ 网络超时 (>10s) → 显示 "网络超时，请重试" → 执行重试逻辑
  ├─ 服务端 500 错误 → 显示 "系统繁忙，请稍后尝试" → 记录错误日志
  └─ 业务校验失败 → 显示具体错误原因 → 高亮对应字段
═════════════════════════════════════════════════════════
```

---

## 6. 预期结果 (Expected Results)

### 6.1 主预期结果（必须全部满足）

| # | 预期结果描述 | 判定标准 | 验证方法 | 阻塞等级 |
|---|------------|---------|---------|---------|
| ER-01 | [结果1] | [具体的判定条件] | Assert/Visual/API/DB-Query | Blocker |
| ER-02 | [结果2] | [具体的判定条件] | Assert/Visual/API/DB-Query | Major |
| ER-03 | [结果3] | [具体的判定条件] | Assert/Visual/API/DB-Query | Minor |

### 6.2 附加验证点（增强信心）

| # | 验证项 | 预期精确值/模式 | 允许偏差 | 验证方法 |
|---|-------|---------------|---------|---------|
| V-001 | [验证项] | `== expected_value` | ±N% / Exact match | Assert |
| V-002 | [验证项] | `matches(pattern)` | Regex match | Assert |
| V-003 | [性能指标] | `< N ms` | ≤ threshold | Performance |

### 6.3 后置状态验证

```yaml
post_state_verification:
  system_state:
    current: "TS-[target_state]"
    previous: "TS-[source_state]"
    
  data_changes:
    - table: "[table_name]"
      operation: "INSERT/UPDATE/DELETE"
      record_count_delta: "+1" / "-N" / 0
      specific_changes:
        "[field]": "[new_value]"  # 从 old → new
        
  external_effects:
    - type: "email/notification/webhook/event_bus"
      expected: "sent with correct payload"
      verification: "check mock/spy/audit_log"
      
  side_effects_to_check:
    - "No unexpected database writes"
    - "Cache properly invalidated/updated"
    - "Audit log entry created"
    - "Metrics/counters incremented correctly"
```

### 6.4 不应该发生的事情 (Negative Assertions)

| # | 不应发生的事 | 为什么重要 | 检测方法 |
|---|-----------|-----------|---------|
| N-01 | 不应返回 500 错误 | 表明服务端未崩溃 | HTTP status code check |
| N-02 | 不应发送重复通知 | 防止用户骚扰 | Notification mock verify called_once |
| N-03 | 不应修改其他用户的数据 | 数据隔离 | DB query other users' records unchanged |

---

## 7. 异常处理分支

| 分支场景 | 触发条件 | 偏离步骤 | 异常现象预期 | 恢复/后续操作 | 回归影响 |
|---------|---------|---------|------------|--------------|---------|
| 网络超时 | 响应 > timeout | Step 3-4 之间 | 显示超时提示 | 可点击「重试」按钮 | 无，原数据保留 |
| 并发冲突 | 数据已被他人修改 | Step 3 之后 | 提示数据已变更 | 选择「刷新」或「强制提交」 | 需重新确认数据 |
| 权限不足 | 会话过期 | 任意步骤 | 重定向到登录页 | 重新登录后回到当前操作 | 需要重新填写部分数据 |
| 输入非法 | 校验失败 | Step 2 之后 | 字段级错误提示 | 修正输入后重新提交 | 仅修正的字段需重新输入 |
| 服务降级 | 外部依赖不可用 | Step 4-5 之间 | 功能受限但核心可用 | 使用缓存/默认值 | 部分功能不可用 |

---

## 8. 清理与还原 (Cleanup / Teardown)

### 8.1 必须执行的清理

| # | 清理操作 | 对象 | 方法 | 时机 |
|---|---------|------|------|------|
| C-01 | 删除测试创建的数据 | Database record | `DELETE FROM table WHERE id = :test_id` | Test End |
| C-02 | 注销测试账号的活跃会话 | Session | `POST /api/auth/logout` | Test End |
| C-03 | 清理上传的测试文件 | File System | `rm -rf /tmp/test_*` | Test End |

### 8.2 还原策略

```yaml
cleanup_strategy:
  mode: "always"  # always / on-failure / never (不推荐)
  
  methods:
    - type: "database_transaction"
      description: "整个用例在一个 DB 事务中执行，结束后 rollback"
      suitable_for: "只读测试或纯业务逻辑测试"
      
    - type: "explicit_cleanup"
      description: "按清理步骤逐一执行"
      suitable_for: "需要验证持久化结果的测试"
      
    - type: "container_reset"
      description: "使用 Docker 容器重建环境"
      suitable_for: "有状态的集成测试"
      
  failure_handling:
    on_cleanup_failure: "Log error + Alert + Continue (不影响用例判定)"
```

---

## 9. 依赖关系

| 依赖类型 | 依赖项 ID | 依赖项名称 | 说明 | 替代方案 |
|---------|----------|-----------|------|---------|
| 前置用例 | TC-[xxx] / None | [title] | 必须先通过此用例 | 无替代 / TC-[yyy] |
| 接口依赖 | API-[endpoint] | `[method] [path]` | 调用的外部接口 | Mock Server / Stub |
| 数据依赖 | Dataset-[name] | [desc] | 需要预加载的测试数据集 | 动态生成 / Factory |
| 环境依赖 | Service-[name] | [desc] | 需要运行的外部服务 | Container / Skip if unavailable |
| 序列依赖 | Sequential | 与 TC-[xxx] 不能并行执行 | 共享资源冲突 | 串行执行队列 |

---

## 10. 自动化适配指南

### 10.1 推荐框架与实现建议

| 层面 | 推荐 | 关键代码片段 | 注意事项 |
|------|------|------------|---------|
| **定位器** | CSS Selector / XPath / TestID | `page.locator('[data-testid="submit-btn"]')` | 优先使用 testid，避免脆弱选择器 |
| **等待策略** | Explicit Wait / Smart Wait | `await page.waitForResponse('**/api/orders')` | 避免 hard-coded sleep |
| **断言库** | Chai / Jest expect / AssertJ | `expect(response.status()).toEqual(201)` | 断言消息要清晰 |
| **数据工厂** | Factory Bot / fixture / builder | `createTestUser({ role: 'regular' })` | 使用 Builder 模式灵活构建 |
| **Mock策略** | MSW / WireMock / pytest-mock | `mockApi.post('/orders').reply(201, {...})` | Mock 数据要与契约一致 |

### 10.2 自动化代码骨架

```python
# === Pytest + Playwright 示例 ===
import pytest
from playwright.sync_api import Page, expect
from factories import create_test_user, create_test_order


@pytest.mark.priority("P0")
@pytest.mark.module("[MODULE]")
@pytest.mark.type("functional")
@pytest.mark.smoke
@pytest.mark.dependency(depends=["TC-[MOD]-[PREV]"], optional=True)
class Test_TC_MOD_NNN:
    """TC-[PHASE]-[MOD]-[NNN]: [用例标题]
    
    Covers: REQ-[xxx], PATH-[yyy], TT-[zzz]
    Estimated: ~N min
    """
    
    @pytest.fixture(autouse=True)
    def setup(self, authenticated_page: Page):
        """前置条件：已认证的页面实例"""
        self.page = authenticated_page
        self.test_user = create_test_user(status="active", role="regular_user")
    
    def test_main_scenario(self):
        """主场景：正常流程"""
        # Step 1: 导航到目标页面
        self.page.goto("/target-page")
        expect(self.page).to_have_title("Expected Title")
        
        # Step 2: 填写表单
        self.page.fill("#field-1", "test_value")
        self.page.select_option("#field-2", "option_value")
        
        # Step 3: 提交
        with self.page.expect_response("**/api/target") as response_info:
            self.page.click("[data-testid='submit-btn']")
        
        response = response_info.value
        assert response.status == 200
        data = response.json()
        
        # Step 4-5: 验证结果
        expect(self.page.locator(".success-message")).to_be_visible()
        expect(self.page.locator(".success-message")).to_contain_text("成功")
        assert data["id"] is not None
        assert data["status"] == "expected_status"
    
    def test_negative_invalid_input(self):
        """负面场景：非法输入"""
        self.page.goto("/target-page")
        self.page.fill("#field-1", "")  # 空值
        self.page.click("[data-testid='submit-btn']")
        
        expect(self.page.locator(".error-message")).to_be_visible()
        expect(self.page.locator(".error-message")).to_contain_text("不能为空")
    
    @pytest.fixture(scope="class")
    def authenticated_page(self, browser: Page) -> Page:
        """返回已完成登录的页面"""
        page = browser.new_page()
        page.goto("/login")
        page.fill("#username", self.test_user.username)
        page.fill("#password", "TestPassword123!")
        page.click("[data-testid='login-btn']")
        page.wait_for_url("**/dashboard")
        yield page
        page.close()
```

### 10.3 CI/CD 集成建议

```yaml
# .github/workflows/test.yml (示例)
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run P0 smoke tests
        run: |
          pytest tests/ \
            -m "priority_p0 and smoke" \
            --junitxml=results/p0-smoke.xml \
            --tb=short \
            -v
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: results/
```

---

## 11. 历史记录

### 11.1 执行历史

| 执行日期 | 执行者 | 环境 | 结果 | 耗时 | 缺陷发现 | 备注 |
|---------|-------|------|------|------|---------|------|
| — | — | — | — | — | — | — |

### 11.2 版本变更历史

| 版本 | 日期 | 作者 | 变更类型 | 变更描述 | 影响评估 | 审批 |
|------|------|------|---------|---------|---------|------|
| 1.0 | YYYY-MM-DD | AI Generator v2.0 | Creation | Initial creation | — | — |

---

*本模板由 testcase-generator v2.0 生成。*
*遵循 IEEE 829 / ISTQB 标准。*
