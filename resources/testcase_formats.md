# 测试用例格式参考 v2.0 (生产级)

> **版本**: 2.0.0 | **用途**: 多场景、多格式的测试用例输出参考
> 本文档定义了 testcase-generator 支持的所有输出格式及其适用场景。

---

## 格式总览

| 格式 ID | 格式名称 | 适用场景 | 可自动化? | 推荐工具 | 复杂度 |
|---------|---------|---------|----------|---------|-------|
| F01 | 标准完整型 | 正式测试交付、合规审计 | ✅ 高 | 任何框架 | ★★★★☆ |
| F02 | 简洁表格型 | 快速评审、Smoke测试 | ⚠️ 中 | 需转换 | ★★☆☆☆ |
| F03 | Gherkin/BDD | 团队协作、行为驱动开发 | ✅ 高 | Cucumber/Behave/Robot | ★★★☆☆ |
| F04 | API 测试型 | 接口测试、契约测试 | ✅ 高 | Postman/REST Assured/Pytest | ★★★★☆ |
| F05 | 数据驱动型 | 参数化批量测试 | ✅ 高 | PyTest-parametrize/DataProvider | ★★★☆☆ |
| F06 | E2E 场景型 | 端到端流程验证 | ✅ 中 | Playwright/Cypress/Selenium | ★★★★☆ |
| F07 | 性能测试型 | 负载/压测/基准测试 | ✅ 高 | k6/JMeter/Gatling | ★★★★☆ |
| F08 | 安全测试型 | 渗透/DAST/SAST | ✅ 高 | OWASP ZAP/Burp Suite | ★★★★★ |

---

## F01: 标准完整格式 (Standard Full Format)

> 最通用的正式格式，适用于所有需要详细记录的场合。这是**默认输出格式**。

### 特点
- 信息最全面，适合作为正式交付物
- 包含完整的追溯信息和元数据
- 可直接转化为自动化脚本
- 符合 IEEE 829 / ISTQB 标准

### 模板结构

```
TC-[PHASE]-[MOD]-[NNN]: [用例标题]
├── 元数据 (metadata)
│   ├── 基本信息 (ID/标题/类型/优先级/模块)
│   ├── 追溯信息 (需求/路径/转换/状态)
│   ├── 自动化信息 (就绪度/框架推荐)
│   └── 变更历史
├── 前置条件 (Preconditions)
│   ├── 系统状态
│   ├── 测试数据准备
│   ├── 环境配置
│   └── 权限认证
├── 测试数据 (Test Data)
│   └── 输入参数表
├── 执行步骤 (Test Steps)
│   └── 步骤表 (操作/对象/输入/预期/验证)
├── 预期结果 (Expected Results)
│   ├── 主预期结果
│   ├── 附加验证点
│   ├── 后置状态验证
│   └── 负向断言
├── 异常处理分支
├── 清理与还原
├── 依赖关系
└── 自动化适配指南 (可选代码骨架)
```

### 示例

```markdown
# TC-AUTH-LOGIN-001: 使用有效凭据通过用户名密码登录成功

## 基本信息
| 属性 | 值 |
|-----|---|
| 用例ID | TC-AUTH-LOGIN-001 |
| 优先级 | 🔴 P0 |
| 类型 | Functional + API |
| 自动化就绪 | Yes (Pytest + Playwright) |

## 前置条件
- 用户已注册且状态为 active
- 测试环境已部署（Staging）
- 认证服务可用

## 测试数据
| 参数 | 值 | 来源 |
|------|-----|------|
| username | "testuser_001" | EQ-V-AUTH-01 |
| password | "Test@Pass2024!" | EQ-V-AUTH-02 |

## 执行步骤
1. POST /api/auth/login { username, password }
2. 验证响应 status = 200
3. 验证响应 body 含 token 字段
4. 验证 token 为有效 JWT 格式
5. 验证用户信息正确返回

## 预期结果
- HTTP 201 Created
- { token: "eyJ...", user: { id, username, role } }
- token 过期时间 = 3600s
```

---

## F02: 简洁表格格式 (Compact Table Format)

> 适用于快速浏览、会议讨论、Smoke测试清单等轻量级场景。

### 特点
- 一行一用例，极简高效
- 适合打印和在屏幕上快速扫描
- 缺少详细信息，不适合独立执行

### 模板

| TC-ID | 标题 | 优先级 | 前置条件 | 步骤摘要 | 预期结果 | 覆盖 |
|-------|------|-------|---------|---------|---------|------|
| TC-001 | [标题] | P0 | [条件] | [1→2→3] | [结果] | REQ-x |

### 示例

| TC-ID | 标题 | P | 前置 | 步骤 | 预期 | 覆盖 |
|-------|------|---|------|------|------|------|
| AUTH-001 | 有效登录 | P0 | 已注册用户 | 输入账号密码→提交 | 登录成功跳转首页 | REQ-001 |
| AUTH-002 | 密码错误 | P1 | 已注册用户 | 输入正确账号+错误密码 | 提示"密码错误" | REQ-001 |
| AUTH-003 | 账号不存在 | P1 | — | 输入不存在的账号 | 提示"账号不存在" | REQ-001 |
| AUTH-004 | 空账号登录 | P2 | — | 不输入账号直接提交 | 提示"请输入账号" | REQ-002 |
| AUTH-005 | 三次锁定 | P1 | 已注册用户 | 连续3次错误密码 | 账号锁定30分钟 | REQ-005 |

---

## F03: Gherkin/BDD 格式 (Behavior Driven Development)

> 适用于敏捷团队、BDD 流程、需要非技术人员可读的场景。

### 特点
- 自然语言风格，业务人员可读
- Given-When-Then 结构清晰
- 直接映射到 Cucumber/Behave/Robot Framework
- 强调行为而非实现

### 模板

```gherkin
Feature: [功能名称]
  As a [角色]
  I want to [行为]
  So that [价值]

  # @priority.P0 @smoke @api
  Scenario: [场景名称]
    Given [前置条件和初始状态]
    When [触发操作]
    Then [可观测的预期结果]
    And [附加验证]

  # @priority.P1 @boundary
  Scenario Outline: [参数化场景名称]
    Given [前置条件]
    When [操作] with "<param>"
    Then [预期结果] should be "<expected>"

    Examples:
      | param | expected |
      | value1 | result1  |
      | value2 | result2  |
```

### 完整示例

```gherkin
Feature: 用户认证登录

  作为一名注册用户，
  我希望通过用户名和密码登录系统，
  以便访问我的个人账户和订单信息。

  # ====== 正向场景 ======

  @priority.P0 @smoke @regression @api
  Scenario: 使用有效的用户名和密码成功登录
    Given 用户 "testuser" 已注册且状态为 "active"
    And 用户的密码是 "Test@Pass2024!"
    And  认证服务正常运行
    When 用户向 "/api/auth/login" 发送 POST 请求，请求体包含:
      """
      {
        "username": "testuser",
        "password": "Test@Pass2024!"
      }
      """
    Then 响应状态码应当是 201
    And  响应体应当包含字段 "token"，且不为空
    And  "token" 应当是有效的 JWT 格式
    And  响应体中的 "user.username" 应当等于 "testuser"
    And  "token" 的过期时间应当在当前时间的 3600 秒之后
    And  数据库 "login_logs" 表应当新增一条记录

  # ====== 异常场景 ======

  @priority.P1 @negative @api
  Scenario: 使用错误的密码登录失败
    Given 用户 "testuser" 已注册
    And  用户的密码不是 "WrongPassword123"
    When 用户尝试用错误密码登录
    Then 响应状态码应当是 401
    And  错误消息应当包含 "密码错误"
    And  响应体不应当包含 "token"
    And  用户的 "failed_login_attempts" 计数增加 1

  # ====== 边界值场景 ======

  @priority.P1 @boundary @api
  Scenario Outline: 用户名边界值登录测试
    Given 存在一名有效用户
    When 用户使用 "<username>" 尝试登录
    Then 应当得到预期响应 "<status>" 和消息 "<message>"

    Examples: 用户名长度边界值
      | username             | status | message           |
      | ""                   | 400    | 用户名不能为空     |
      | "a"                  | 200    | 登录成功          |  # 最小长度
      | {"a"*200}            | 200    | 登录成功          |  # 最大长度
      | {"a"*201}            | 400    | 用户名超长        |  # 超最大长度 |
      | "<script>alert(1)</script>" | 400 | 含非法字符   |  # XSS防护 |

  # ====== 安全场景 ====== 

  @priority.P0 @security @api
  Scenario: 防止暴力破解 - 多次失败后锁定账户
    Given 用户 "testuser" 当前 failed_login_attempts = 2
    And  账户锁定阈值为 3 次
    And  锁定时间为 30 分钟
    When 用户连续第 3 次使用错误密码登录
    Then 响应状态码应当是 401
    And  错误消息应当包含 "账户已被临时锁定"
    And  用户的 account_status 应当变为 "locked"
    And  解锁时间应当设置为当前时间 + 30 分钟
    When 在锁定期间再次尝试登录
    Then 响应状态码应当是 403
    And  错误消息应当包含 "账户已锁定"

  # ====== 并发场景 ======

  @priority.P2 @concurrency @api
  Scenario: 同一账号不允许重复登录（互踢）
    Given 用户 "testuser" 已在设备A上登录，持有 token_A
    When 用户在设备B上使用相同凭据重新登录
    Then 设备B应当获得新的 token_B
    And  设备A的 token_A 应当失效
    When 设备A使用 token_A 访问受保护资源
    Then 响应状态码应当是 401
    And  错误消息应当包含 "登录已过期"
```

---

## F04: API 测试格式 (API Testing Format)

> 专门针对 RESTful / GraphQL / gRPC / WebSocket API 的测试格式。

### 特点
- 专注于 request/response 的精确匹配
- 包含完整的 HTTP 细节
- 天然适合自动化（Postman/Newman/REST Assured）
- 支持契约测试（Pact/OpenAPI）

### 模板

```markdown
## API Test: [METHOD] [Endpoint]

### Metadata
- **TC-ID**: TC-API-[NNN]
- **Priority**: P0-P3
- **Category**: Happy / Auth / Validation / Error / Edge / Security / Performance

### Request
- **Method**: GET / POST / PUT / DELETE / PATCH
- **URL**: `{base_url}/api/{version}/{resource}`
- **Headers**:
  ```
  Content-Type: application/json
  Authorization: Bearer {token}
  X-Request-ID: {uuid}
  Accept-Language: zh-CN
  ```
- **Query Params** (if GET):
  ```
  ?page=1&size=20&sort=created_at:desc
  ```
- **Request Body** (if POST/PUT/PATCH):
  ```json
  {
    "field1": "value1",
    "field2": { "nested": "value" },
    "field3": ["item1", "item2"]
  }
  ```

### Expected Response
- **Status Code**: 200 / 201 / 204 / 400 / 401 / 403 / 404 / 409 / 500
- **Response Headers**:
  ```
  Content-Type: application/json
  X-RateLimit-Remaining: 99
  ```
- **Response Body Schema**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "$ref": "#/definitions/ResponseData"
    }
  }
  ```

### Test Scenarios Matrix
| Scenario | Key Input(s) | Expected Code | Expected Message | Special Asserts |
|----------|-------------|---------------|-----------------|----------------|
| Normal | Valid inputs | 200/201 | success | Data correctness |
| Empty field | field="" | 400 | Field required | Error in errors[] |
| Invalid type | field=123 (expect str) | 422 | Type mismatch | Detailed error |
| Unauth | No token | 401 | Unauthorized | WWW-Authenticate header |
| Forbidden | Valid token, wrong role | 403 | Forbidden | — |
| Not found | resource_id=nonexistent | 404 | Not found | — |
| Conflict | Duplicate unique key | 409 | Already exists | Error details |
| Rate limit | >100 req/min | 429 | Too many requests | Retry-After header |

### Contract Assertions
```javascript
// Example using chai-json-schema
const response = await api.request(options);
expect(response.status).to.equal(200);
expect(response.body).to.jsonSchema(apiSchema);
expect(response.body.data.id).to.be.a('string').and.match(/^[0-9a-f]{24}$/);
expect(response.headers['x-request-id']).to.exist;
```
```

### Postman Collection 示例

```json
{
  "info": { "name": "Auth API Tests", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "variable": [
    { "key": "baseUrl", "value": "https://api-staging.example.com" },
    { "key": "accessToken", "value": "" }
  ],
  "item": [{
    "name": "TC-API-001: Successful Login",
    "event": [{"listen": "test", "script": { "exec": [
      "pm.test('Status is 201', () => pm.response.to.have.status(201));",
      "pm.test('Has valid token', () => {",
      "  const json = pm.response.json();",
      "  expect(json.data.token).to.be.a('string');",
      "  const payload = JSON.parse(atob(json.data.token.split('.')[1]));",
      "  expect(payload.exp).to.be.above(Date.now()/1000);",
      "});",
      "pm.collectionVariables.set('accessToken', pm.response.json().data.token);"
    ]}}],
    "request": {
      "method": "POST",
      "header": [{ "key": "Content-Type", "value": "application/json" }],
      "body": { "mode": "raw", "raw": "{\n  \"username\": \"{{username}}\",\n  \"password\": \"{{password}}\"\n}" },
      "url": { "raw": "{{baseUrl}}/v1/auth/login" }
    }
  }]
}
```

---

## F05: 数据驱动格式 (Data-Driven Testing)

> 适用于有大量相似测试数据、需要参数化的批量测试场景。

### 特点
- 测试逻辑与测试数据分离
- 单个模板 + 大量数据组合
- 极高的维护效率
- 天然支持 Excel/CSV/JSON/YAML 数据源

### Python Pytest 示例

```python
import pytest
from datetime import timedelta


# ====== 数据定义 ======
@pytest.fixture
def registered_user():
    return {"username": "datadriven_user", "password": "ValidPass123!"}


# ====== 登录边界值测试数据 ======
LOGIN_BOUNDARY_DATA = [
    # (username, password, expected_code, expected_msg, description)
    ("",              "ValidPass123!", 400, "用户名不能为空",       "空用户名"),
    ("   ",           "ValidPass123!", 400, "用户名不能为空白",    "纯空白"),
    ("a",             "ValidPass123!", 200, "success",             "最小长度用户名"),
    ("valid_user",    "",              400, "密码不能为空",         "空密码"),
    ("valid_user",    "short",         400, "密码至少8位",         "密码过短"),
    ("valid_user",    "ValidPass123!", 200, "success",             "正常登录"),
    ("x" * 50,        "ValidPass123!", 200, "success",             "最大长度用户名"),
    ("x" * 51,        "ValidPass123!", 400, "用户名过长",          "超过最大长度"),
    ("<script>x</>",  "ValidPass123!", 400, "含非法字符",         "XSS注入"),
    ("'; DROP TABLE--","ValidPass123!", 400, "含非法字符",         "SQL注入"),
    ("valid_user",    None,            400, "缺少password字段",    "缺少字段"),
]


@pytest.mark.priority("P1")
@pytest.mark.boundary
@pytest.mark.parametrize("username,password,expected_code,expected_msg,desc", LOGIN_BOUNDARY_DATA, ids=[d[4] for d in LOGIN_BOUNDARY_DATA])
def test_login_boundary_values(registered_user, client, username, password, expected_code, expected_msg, desc):
    """TC-AUTH-LOGIN-BV: 登录接口边界值测试
    
    Covers: Phase 1 Boundary Conditions (BVA-001 through BVA-010)
    """
    payload = {"username": username}
    if password is not None:
        payload["password"] = password
    
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == expected_code, f"[{desc}] Expected {expected_code}, got {response.status_code}"
    
    data = response.json()
    if expected_code == 200:
        assert "token" in data, "[{}] Response should contain token".format(desc)
        assert data["message"] == "success", "[{}] Unexpected message".format(desc)
    else:
        assert expected_msg in data["message"], \
            '[{}] Expected error msg containing "{}", got "{}"'.format(desc, expected_msg, data.get("message"))


# ====== 密码策略测试数据 ======
PASSWORD_POLICY_DATA = [
    # (password,                    expected_valid, reason)
    ("Abc123!@",                    True,   "符合所有规则"),
    ("abc123!@",                    False,  "缺少大写字母"),
    ("ABC123!@",                    False,  "缺少小写字母"),
    ("Abcdef!@",                    False,  "缺少数字"),
    ("Abc12345",                    False,  "缺少特殊字符"),
    ("Ab1!@#",                      False,  "少于8位"),
    ("Abcdefg123!@#$%",           True,   "较长但合法"),
    ("Password123!",               True,   "常见模式但允许"),
    ("p@$$w0rd",                    True,   "leet speak 允许"),
    ("aaaaaaaa",                    False,  "纯小写无特殊"),
]


@pytest.mark.parametrize("password,expected,reason", PASSWORD_POLICY_DATA)
def test_password_policy_validation(client, password, expected, reason):
    """TC-AUTH-PW-POLICY: 密码复杂度策略验证"""
    response = client.post("/api/auth/register", json={
        "username": "new_user",
        "password": password,
        "email": "new@test.com"
    })
    
    if expected:
        assert response.status_code in [200, 201], f"[{reason}] Should accept valid password"
    else:
        assert response.status_code == 400, f"[{reason}] Should reject invalid password"
        assert "password" in str(response.json()).lower(), \
            f"[{reason}] Error should mention password"


# ====== 从 CSV/Excel 加载数据 ======
@pytest.fixture
def csv_test_data():
    import csv
    from io import StringIO
    
    csv_data = """username,password,expected_code,test_type
admin,Admin123!,200,happy
guest,Guest123!,200,happy
locked,Locked123!,403,locked_account
expired,Expired123!,401,token_expired"""
    
    reader = csv.DictReader(StringIO(csv_data))
    return list(reader)


@pytest.mark.parametrize("row", csv_test_data(), indirect=True)
def test_login_from_csv(client, row):
    """从外部数据文件驱动的登录测试"""
    response = client.post("/api/auth/login", json={
        "username": row["username"],
        "password": row["password"]
    })
    assert response.status_code == int(row["expected_code"])
```

---

## F06: E2E 场景测试格式 (End-to-End Scenario)

> 适用于跨多个系统/页面/服务的端到端流程验证。

### 特点
- 关注完整业务流程而非单点功能
- 涉及多个页面、API、数据库的协同
- 强调真实用户体验路径
- 通常需要复杂的测试数据准备

### 模板

```markdown
## E2E Scenario: [场景名称]

### 场景元信息
- **TC-ID**: TC-E2E-[NNN]
- **优先级**: P0-P3
- **涉及页面/API**: 
  1. [Page/API 1]
  2. [Page/API 2]
  3. ...
- **预估执行时间**: N 分钟
- **数据清理级别**: Full Cleanup / Soft Delete / Keep for Audit

### 用户故事
```
As a [role],
I want to [complete flow],
So that [achieve business value].
```

### 完整链路图
```
[入口] → [步骤1] → [步骤2] → ... → [步骤N] → [出口]
  │         │         │               │         │
  ▼         ▼         ▼               ▼         ▼
[Page A]  [API X]  [DB Write]      [Async Job]  [Result Page]
```

### 详细步骤
| Step | 页面/API | 操作 | 验证点 | 数据检查 |
|------|---------|------|--------|---------|
| 1 | Landing Page | 点击「开始」 | 跳转到 Step1 | — |
| 2 | Form Page | 填写并提交 | 表单校验通过 | DB: draft created |
| 3 | Confirm Page | 确认信息 | 信息展示正确 | — |
| 4 | Payment | 选择支付方式 | 跳转支付页 | — |
| 5 | Payment Callback | 支付完成回调 | 订单状态变更 | DB: order=paid |
| 6 | Result Page | 展示成功页 | 成功信息正确 | Email sent? |

### Playwright 自动化示例
```typescript
import { test, expect } from '@playwright/test';

test.describe('E2E: 完整购物流程', () => {

  test.beforeEach(async ({ page }) => {
    // 全局前置：登录
    await page.goto('/login');
    await page.fill('#username', 'e2e_test_user');
    await page.fill('#password', 'E2ETestPass!');
    await page.click('[data-testid="login-btn"]');
    await page.waitForURL('**/dashboard');
  });

  test('完整购买流程: 浏览→加购→结算→支付→完成', async ({ page }) => {
    // Step 1: 浏览商品列表
    await page.goto('/products');
    await expect(page.locator('.product-list')).toBeVisible();
    
    // Step 2: 搜索商品
    await page.fill('[data-testid="search-input"]', 'iPhone 15');
    await page.press('[data-testid="search-input"]', 'Enter');
    await expect(page.locator('.product-card')).toHaveCount({ min: 1 });
    
    // Step 3: 加入购物车
    await page.click('[data-testid="add-to-cart"]:first-child');
    await expect(page.locator('.cart-badge')).toContainText('1');
    
    // Step 4: 进入购物车
    await page.click('[data-testid="cart-icon"]');
    await expect(page).toHaveURL(/\/cart/);
    await expect(page.locator('.cart-item')).toHaveCount(1);
    
    // Step 5: 结算
    await page.click('[data-testid="checkout-btn"]');
    await expect(page).toHaveURL(/\/checkout/);
    
    // Step 6: 选择地址
    await page.selectOption('[name="address_id']", 'addr_001');
    await page.click('[data-testid="next-step"]');
    
    // Step 7: 选择支付方式
    await page.click('[data-testid="pay-alipay"]');
    await page.click('[data-testid="submit-payment"]');
    
    // Step 8: Mock 支付回调
    // (在实际 E2E 中可能需要 mock 或使用沙盒支付)
    await page.route('**/api/payment/callback/**', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ trade_no: 'mock_trade_001', status: 'SUCCESS' })
    }));
    
    // Step 9: 验证订单完成页
    await expect(page).toHaveURL(/\/order\/.*\/success/, { timeout: 15000 });
    await expect(page.locator('[data-testid="order-success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="order-id"]')).not.toBeEmpty();
    
    // Step 10: 数据库最终验证 (via API)
    const orderId = await page.locator('[data-testid="order-id"]').textContent();
    const orderResponse = await page.request.get(`/api/orders/${orderId}`);
    expect(orderResponse.status()).toBe(200);
    const orderData = await orderResponse.json();
    expect(orderData.data.status).toBe('PAID');
    expect(orderData.data.payment_method).toBe('ALIPAY');
    expect(orderData.data.items).toHaveLength(1);
  });
});
```

---

## 格式选择指南

### 决策树

```
你的测试场景是什么？
│
├─ 需要交付给客户/第三方审计？
│   └─→ F01 标准完整格式 ✓
│
├─ 团队使用 BDD / 需要 PO 可读？
│   └─→ F03 Gherkin 格式 ✓
│
├─ 纯 API 接口测试？
│   └─→ F04 API 测试格式 ✓
│
├─ 大量相似的参数化测试？
│   └─→ F05 数据驱动格式 ✓
│
├─ 跨系统的端到端流程？
│   └─→ F06 E2E 场景格式 ✓
│
├─ 只需要一个快速参考清单？
│   └─→ F02 简洁表格格式 ✓
│
└─ 其他情况？
    └─→ F01 标准完整格式（默认）✓
```

### 格式对比矩阵

| 维度 | F01标准 | F02简洁 | F03-Gherkin | F04-API | F05-数据驱动 | F06-E2E |
|------|--------|---------|-------------|--------|------------|--------|
| **信息完整度** | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **可读性(非技术人员)** | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★★★☆ |
| **自动化转化难度** | 低 | 中 | 低 | 极低 | 极低 | 中 |
| **维护效率** | 中 | 高 | 高 | 高 | 极高 | 中 |
| **适合团队规模** | 任意 | 小型 | 敏捷/大型 | 技术导向 | 任意 | 全栈 |
| **适合项目阶段** | 所有阶段 | 执行阶段 | 设计+执行阶段 | 开发+测试 | 回归测试 | 验收测试 |

---

*本格式指南由 testcase-generator v2.0 提供。*
*根据实际项目需求选择最适合的格式，或混合使用多种格式。*
