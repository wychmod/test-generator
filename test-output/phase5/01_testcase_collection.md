---
document_type: "testcase"
template_version: "2.0.0"
generated_by: "testcase-generator v2.0.0"
metadata:
  testcase_id: "TC-AUTH-LOGIN-001"
  version: "1.0"
  status: "Draft"
  created: "2026-04-04T15:05:00+08:00"
  last_modified: "2026-04-04T15:05:00+08:00"
  author: "AI Generator v2.0"
  reviewer: ""
  approver: ""
  automation:
    ready: "Yes"
    framework_recommendation: "Pytest + Playwright"
    implementation_status: "Not-Started"
  priority: "P0"
  execution:
    estimated_duration_minutes: 3
    actual_duration_minutes: null
    last_execution_date: null
    last_execution_result: null
    total_executions: 0
    pass_rate: null
traceability:
  requirements: ["REQ-001"]
  paths: ["PATH-001"]
  transitions: ["TT-LOGIN-001"]
  states: ["S-LOGGED_OUT"]
  defects: []
change_history:
  - version: "1.0"
    date: "2026-04-04"
    author: "AI Generator v2.0"
    change: "Initial creation from PRD analysis"
---

# TC-AUTH-LOGIN-001: 使用有效凭据通过用户名密码登录成功

## 1. 基本信息卡

### 1.1 核心属性

| 属性 | 值 |
|-----|---|
| **用例ID** | TC-AUTH-LOGIN-001 |
| **用例标题** | 验证已注册用户在账户正常状态下使用正确用户名密码登录成功 |
| **测试类型** | ☑ Functional ☑ API |
| **测试子类型** | Happy-Path |
| **优先级** | 🔴 **P0** (阻塞) |
| **所属模块** | 用户登录模块 / F-010-01 |
| **所属套件** | TS-AUTH |
| **复杂度** | ⭐ Simple (≤3步) |

### 1.2 分类标签

```
Tags: auth, login, smoke, P0, positive, happy-path, regression
```

---

## 2. 需求追溯

### 2.1 正向追溯（本用例覆盖了什么）

| 追溯类型 | ID | 描述 | 覆盖方式 | 验证方法 |
|---------|-----|------|---------|---------|
| **需求** | REQ-001 | 用户名密码登录 | Direct | API响应验证 |
| **路径** | PATH-001 | 正常登录流程 | Full | 完整步骤覆盖 |
| **转换** | TT-LOGIN-001 | 未登录→已登录 | Entry | Session创建验证 |

### 2.2 独占贡献（本用例独有的覆盖价值）

- 验证登录成功后的完整响应结构（包含Token和用户信息）
- 验证Session正确创建并可用于后续请求

### 2.3 反向追溯（如果移除此用例的影响）

| 影响维度 | 当前覆盖情况 | 移除后 | 风险评估 |
|---------|------------|--------|---------|
| REQ-001 核心路径 | 由 TC-AUTH-LOGIN-001 独占 | ❌ 失去核心功能验证 | 🔴 高风险 |

---

## 3. 前置条件 (Preconditions)

### 3.1 系统状态

```
✅ 系统必须处于以下状态：
   · 当前实体状态: S-LOGGED_OUT (未登录状态)
   · 测试用户已存在于数据库且状态为 active
   · 认证服务正常运行

❌ 系统不得处于以下状态：
   · 用户账户已被锁定
   · 存在活跃Session
```

### 3.2 测试数据准备

| 数据ID | 数据描述 | 类型 | 准备方式 | 数量 |
|-------|---------|------|---------|------|
| DATA-001 | 测试用户 | Master | Pre-created | 1 |

**详细数据规格**:

```yaml
DATA-001:
  entity: User
  attributes:
    id: "auto-generated"
    username: "testuser_001"
    email: "testuser@example.com"
    password: "Test@Pass2024!"  # BCrypt加密存储
    status: "active"
    role: "regular_user"
  cleanup_strategy: "soft_delete"
```

### 3.3 环境配置

| 维度 | 要求 | 验证命令/方法 |
|------|------|-------------|
| API 环境 | Staging | `curl https://api-staging.example.com/health` |
| 数据库 | 测试数据库 (test_db) | `SELECT count(*) FROM users WHERE username='testuser_001'` |

---

## 4. 测试数据 (Test Data)

### 4.1 输入数据表

| 参数# | 参数名 | 参数类型 | 测试值 | 格式要求 | 敏感度 |
|-------|-------|---------|--------|---------|-------|
| 1 | username | String | `testuser_001` | 4-20字符 | Public |
| 2 | password | String | `Test@Pass2024!` | 至少8位 | Confidential |
| 3 | remember_me | Boolean | `false` | - | Public |

---

## 5. 执行步骤 (Test Steps)

### 5.1 步骤表

| 步骤# | 操作类别 | 操作描述 | 操作对象 | 详细操作 | 输入数据 | 预期结果 | 验证方式 |
|-------|---------|---------|---------|---------|---------|---------|---------|
| 1 | API Request | 发送登录请求 | POST /api/auth/login | `POST /api/auth/login` | `{ username, password }` | HTTP 200 | Status Code |
| 2 | Verify Response | 验证Token存在 | Response Body | 检查 token 字段 | — | token 不为空且为JWT格式 | JSON Assert |
| 3 | Verify User Info | 验证用户信息 | Response Body | 检查 user 对象 | — | username=输入值, status=active | JSON Assert |
| 4 | Verify Headers | 验证响应头 | Response Headers | 检查Session设置 | — | Set-Cookie 包含 session_id | Header Check |

### 5.2 步骤详细说明

```
═════════════════════════════════════════════════════════
Step 1: 发送登录请求
═════════════════════════════════════════════════════════

请求详情:
  · Method: POST
  · URL: https://api-staging.example.com/api/auth/login
  · Headers:
      Content-Type: application/json
      Accept: application/json
  · Body:
      {
        "username": "testuser_001",
        "password": "Test@Pass2024!"
      }

预期响应:
  HTTP 201 Created
  Body:
      {
        "code": 0,
        "message": "success",
        "data": {
          "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "expires_in": 3600,
          "user": {
            "id": "usr_xxxxx",
            "username": "testuser_001",
            "email": "testuser@example.com",
            "role": "regular_user"
          }
        }
      }

═════════════════════════════════════════════════════════
Step 2-4: 验证响应完整性
═════════════════════════════════════════════════════════

验证点清单:
  ☐ HTTP 状态码为 201
  ☐ Response body 包含 code=0
  ☐ Response body 包含 message="success"
  ☐ Response body.data.token 不为 null
  ☐ Response body.data.token 为有效 JWT 格式 (3段式)
  ☐ Response body.data.expires_in = 3600
  ☐ Response body.data.user.username = "testuser_001"
  ☐ Response body.data.user.email = "testuser@example.com"
  ☐ Response body.data.user.status = "active"
  ☐ Set-Cookie 包含 session_id
═════════════════════════════════════════════════════════
```

---

## 6. 预期结果 (Expected Results)

### 6.1 主预期结果（必须全部满足）

| # | 预期结果描述 | 判定标准 | 验证方法 | 阻塞等级 |
|---|------------|---------|---------|---------|
| ER-01 | HTTP 状态码为 201 Created | `response.status == 201` | Assert | Blocker |
| ER-02 | 响应包含有效 Token | `data.token != null && data.token.length > 0` | Assert | Blocker |
| ER-03 | Token 为 JWT 格式 | `token.split('.').length == 3` | Assert | Major |
| ER-04 | 用户信息正确返回 | `user.username == "testuser_001"` | Assert | Major |

### 6.2 附加验证点（增强信心）

| # | 验证项 | 预期精确值/模式 | 允许偏差 | 验证方法 |
|---|-------|---------------|---------|---------|
| V-001 | Token 过期时间 | `3600` 秒 (1小时) | Exact match | Assert |
| V-002 | 用户角色 | `regular_user` | Exact match | Assert |
| V-003 | 用户状态 | `active` | Exact match | Assert |

### 6.3 后置状态验证

```yaml
post_state_verification:
  system_state:
    current: "S-LOGGED_IN"
    previous: "S-LOGGED_OUT"

  data_changes:
    - table: "login_logs"
      operation: "INSERT"
      record_count_delta: "+1"
      specific_changes:
        "user_id": "usr_xxxxx"
        "login_at": "{current_timestamp}"
        "ip_address": "{test_client_ip}"

  external_effects:
    - type: "email/notification"
      expected: "无触发"
      verification: "notification_service.get_call_count() == 0"
```

---

## 7. 异常处理分支

| 分支场景 | 触发条件 | 偏离步骤 | 异常现象预期 | 恢复/后续操作 |
|---------|---------|---------|------------|--------------|
| 网络超时 | 响应 > 10s | Step 1 | 显示"网络超时" | 执行重试逻辑 |
| 服务端 500 | HTTP 500 | Step 1 | 显示"系统繁忙" | 记录错误日志 |
| 密码已修改 | 密码已被他人修改 | Step 1 | 提示"密码错误" | 无（这是正常失败）|

---

## 8. 清理与还原 (Cleanup)

| # | 清理操作 | 对象 | 方法 | 时机 |
|---|---------|------|------|------|
| C-01 | 清除登录日志 | login_logs | `DELETE FROM login_logs WHERE user_id='usr_xxxxx'` | Test End |
| C-02 | 可选：清除Session | Redis | `DEL session:{session_id}` | Test End |

---

## 9. 自动化适配指南

### 推荐框架与实现建议

| 层面 | 推荐 | 关键代码片段 |
|------|------|------------|
| **测试框架** | Pytest | `@pytest.mark.auth` |
| **HTTP Client** | requests / httpx | `client.post("/api/auth/login", json=payload)` |
| **断言库** | pytest-assert | `assert response.status_code == 201` |
| **数据工厂** | Factory Bot | `create_test_user()` |

### 自动化代码骨架

```python
import pytest
from requests import Session


@pytest.mark.priority("P0")
@pytest.mark.smoke
@pytest.mark.auth
class TestLoginSuccess:
    """TC-AUTH-LOGIN-001: 使用有效凭据登录成功"""

    @pytest.fixture
    def api_client(self):
        return Session(base_url="https://api-staging.example.com")

    @pytest.fixture
    def test_user(self):
        return {
            "username": "testuser_001",
            "password": "Test@Pass2024!"
        }

    def test_login_with_valid_credentials(self, api_client, test_user):
        """验证已注册用户使用正确凭据登录成功"""
        response = api_client.post("/api/auth/login", json=test_user)

        # ER-01: 验证状态码
        assert response.status_code == 201, \
            f"Expected 201, got {response.status_code}"

        data = response.json()

        # ER-02: 验证 Token 存在
        assert "token" in data["data"], "Token should be present"
        assert data["data"]["token"], "Token should not be empty"

        # ER-03: 验证 JWT 格式
        token_parts = data["data"]["token"].split(".")
        assert len(token_parts) == 3, "Token should be valid JWT format"

        # ER-04: 验证用户信息
        user = data["data"]["user"]
        assert user["username"] == test_user["username"]
        assert user["status"] == "active"

        # V-001: 验证过期时间
        assert data["data"]["expires_in"] == 3600
```

---

## 10. 执行历史

| 执行日期 | 执行者 | 环境 | 结果 | 耗时 | 缺陷发现 | 备注 |
|---------|-------|------|------|------|---------|------|
| — | — | — | — | — | — | — |
