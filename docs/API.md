# AI Goal Coach API 接口文档

**版本**: 1.1  
**最后更新**: 2026-04-03  
**服务地址**: http://localhost:8001/api/v1

---

## 目录

1. [系统架构](#系统架构)
2. [前后端职责边界](#前后端职责边界)
3. [认证接口](#认证接口)
4. [目标接口](#目标接口)
5. [打卡接口](#打卡接口)
6. [学习伙伴接口](#学习伙伴接口)
7. [错误处理](#错误处理)
8. [数据字典](#数据字典)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Flutter)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  用户界面层  │  │  状态管理   │  │  本地数据存储 (Hive)    │  │
│  │  - 登录注册  │  │  - Provider │  │  - User 缓存            │  │
│  │  - 目标列表  │  │  - 数据刷新 │  │  - Goal 缓存            │  │
│  │  - 打卡界面  │  │  - 错误处理 │  │  - Token 存储           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/HTTPS (JWT 认证)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端 (FastAPI)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  API 路由层  │  │  业务逻辑层  │  │  数据访问层 (SQLAlchemy)│  │
│  │  - 认证     │  │  - AI 教练   │  │  - User Repository      │  │
│  │  - 目标     │  │  - 打卡逻辑  │  │  - Goal Repository      │  │
│  │  - 打卡     │  │  - 进度计算  │  │  - Checkin Repository   │  │
│  │  - 伙伴     │  │  - 权限验证  │  │  - Partner Repository   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                              │                                   │
│                       ┌──────▼──────┐                           │
│                       │  PostgreSQL  │                           │
│                       │   Database   │                           │
│                       └─────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              │                   ┌───────────────┐
                              ▼                   │   Redis       │
┌─────────────────────────────────────────────────┤   - 验证码    │
│                       外部服务                   │   - 过期删除  │
│  ┌─────────────────┐  ┌──────────────────────┐  └───────────────┘
│  │  Alibaba        │  │   SMTP 邮件服务      │
│  │  DashScope      │  │   - 验证码邮件       │
│  │  (qwen3.5-plus) │  │   - 通知邮件         │
│  └─────────────────┘  └──────────────────────┘
```

---

## 前后端职责边界

### 职责划分原则

| 职责 | 前端 | 后端 | 说明 |
|------|------|------|------|
| **用户认证** | 存储 Token、自动续期 | 签发 Token、验证权限 | 前端负责本地存储，后端负责验证 |
| **数据展示** | 渲染 UI、本地缓存 | 数据聚合、分页 | 前端决定如何展示，后端决定返回什么 |
| **业务规则** | 表单验证、输入校验 | 核心规则、权限检查 | 前端防错，后端兜底 |
| **进度计算** | 实时显示、动画 | 持久化、一致性 | 前端可缓存，后端为准 |
| **AI 交互** | 展示 AI 内容 | 调用 AI、内容过滤 | 前端只展示，后端处理 AI |
| **错误处理** | 用户友好提示 | 日志记录、错误分类 | 前端安抚用户，后端记录问题 |

### 详细职责边界

#### 前端职责（Flutter）

**必须做的：**
1. **Token 管理**
   - 安全存储 `access_token` 和 `refresh_token`
   - Token 过期时自动调用刷新接口
   - 刷新失败时退出登录

2. **本地状态管理**
   - 缓存用户数据、目标列表
   - 乐观更新（打卡后先更新 UI，再同步后端）
   - 处理离线状态

3. **用户输入验证**
   - 表单格式检查（邮箱、密码强度）
   - 日期范围校验（结束日期 > 开始日期）
   - 必填字段检查

4. **错误展示**
   - 将后端错误码转化为用户友好提示
   - 网络错误重试机制
   - 加载状态展示

**不应该做的：**
- 不信任后端返回的数据（仍需校验）
- 不存储敏感信息（密码、完整用户数据）
- 不绕过后端直接修改数据库

#### 后端职责（FastAPI）

**必须做的：**
1. **数据验证**
   - 所有输入参数验证（Pydantic Schema）
   - 业务规则验证（日期范围、权限检查）
   - 数据一致性保证（事务）

2. **权限控制**
   - JWT Token 验证
   - 资源所有权验证（用户只能访问自己的数据）
   - 操作权限验证（如每天只能打卡一次）

3. **业务逻辑**
   - 进度计算（`current_day`、`progress`）
   - 连续打卡天数计算
   - AI 内容生成和过滤

4. **数据聚合**
   - 列表接口返回分页数据
   - 复杂查询优化（避免 N+1）
   - 返回前端需要的完整数据（减少 frontend 计算）

**不应该做的：**
- 不存储前端状态（由前端管理）
- 不处理 UI 逻辑（如动画、路由）
- 不返回无关数据（隐私保护）

### 数据流示例

#### 打卡流程

```
前端                          后端                          AI 服务
 │                              │                              │
 ├─ 1. 提交打卡 ───────────────►│                              │
 │    {goal_id, notes,          │                              │
 │     mood_rating}             │                              │
 │                              │                              │
 │                              ├─ 2. 验证权限 ───────────────►│
 │                              │    - Token 有效？              │
 │                              │    - 目标存在？                │
 │                              │    - 今天已打卡？              │
 │                              │                              │
 │                              ├─ 3. 计算 streak_count ─────►│
 │                              │                              │
 │                              ├─ 4. 生成 AI 点评 ───────────►│
 │                              │    {feedback, suggestion}    │
 │                              │◄─────────────────────────────┤
 │                              │                              │
 │                              │ 5. 保存打卡记录               │
 │                              │    - Checkin.create()        │
 │                              │    - goal.current_day += 1   │
 │                              │                              │
 │                              │ 6. 查询 next task             │
 │                              │    today_task = Task[day+1]  │
 │                              │                              │
 │◄─ 7. 返回完整响应 ──────────┤                              │
 │    {                         │                              │
 │      id, streak_count,       │                              │
 │      ai_feedback,            │                              │
 │      goal: {                 │                              │
 │        current_day,          │                              │
 │        duration_days,        │                              │
 │        progress,             │                              │
 │        today_task            │                              │
 │      }                       │                              │
 │    }                         │                              │
 │                              │                              │
 ├─ 8. 更新本地状态              │                              │
 │    - 显示进度条更新           │                              │
 │    - 显示 AI 点评             │                              │
 │    - 刷新目标列表             │                              │
 │                              │                              │
```

**关键点：**
- 前端提交最小程序（只提交用户输入）
- 后端返回完整数据（减少 frontend 计算和额外请求）
- 打卡接口返回更新后的 `goal` 对象，前端无需额外调用

---

## 认证接口

### 1. 发送邮箱验证码

```
POST /api/v1/auth/send-verification-code
```

**请求体：**
```json
{
  "email": "user@example.com"
}
```

**响应 (200 OK)：**
```json
{
  "message": "验证码已发送到邮箱，10 分钟内有效"
}
```

**前端职责：**
- 在用户输入邮箱后调用此接口
- 展示验证码输入框，等待用户输入
- 验证码过期后允许重新发送

**后端职责：**
- 生成 6 位数字验证码
- 存储验证码到 Redis（10 分钟过期）
- 发送验证码邮件（当前为模拟发送，打印到日志）

**错误响应：**
- 400 - 该邮箱已被注册

---

### 2. 验证邮箱（可选）

```
POST /api/v1/auth/verify-email
```

**请求体：**
```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

**响应 (200 OK)：**
```json
{
  "message": "邮箱验证成功"
}
```

**说明：** 此接口为可选，前端也可在注册时直接提交 `verification_code`。

**错误响应：**
- 400 - 验证码错误或已过期

---

### 3. 用户注册

```
POST /api/v1/auth/register
```

**请求体：**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "verification_code": "123456"
}
```

**响应 (201 Created)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**前端职责：**
- 验证邮箱格式、密码强度（前端校验）
- 安全存储返回的 Token
- 注册成功后自动登录

**后端职责：**
- 验证邮箱验证码有效性
- 验证邮箱、用户名唯一性
- 密码加密存储（bcrypt）
- 签发 JWT Token

**错误响应：**
- 400 - 该邮箱已被注册 / 该用户名已被使用 / 邮箱验证码错误或已过期

---

### 4. 用户登录

```
POST /api/v1/auth/login
```

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应 (200 OK)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**前端职责：**
- 记住登录状态
- 持久化 Token

**后端职责：**
- 验证密码
- 签发 Token

**错误响应：**
- 401 - 邮箱或密码错误

---

### 5. 刷新 Token

```
POST /api/v1/auth/refresh
```

**请求体：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应 (200 OK)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**前端职责：**
- 检测 access_token 过期（401 响应）
- 自动调用刷新接口
- 刷新失败时退出登录

**后端职责：**
- 验证 refresh_token 有效性
- 签发新 Token 对

**错误响应：**
- 401 - 无效的 Refresh Token / 用户不存在

---

### 6. 获取当前用户信息

```
GET /api/v1/auth/me
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "username",
  "avatar_url": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**前端职责：**
- 展示用户信息
- 本地缓存减少请求

**后端职责：**
- 验证 Token
- 返回用户信息

---

### 7. 用户登出

```
POST /api/v1/auth/logout
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
  "message": "已成功登出"
}
```

**前端职责：**
- 清除本地 Token
- 返回登录页

**后端职责：**
- JWT 无状态，无需操作（可选：加入黑名单）

---

### 邮箱验证流程

```
前端                          后端                          Redis
 │                              │                              │
 ├─ 1. 输入邮箱 ──────────────►│                              │
 │                              │                              │
 ├─ 2. 发送验证码 ────────────►│                              │
 │    {email}                   │                              │
 │                              │                              │
 │                              ├─ 3. 生成验证码 ────────────►│
 │                              │    code = "123456"           │
 │                              │    setex(email, 10min)       │
 │                              │                              │
 │                              ├─ 4. 发送邮件 ◄─────────────┤
 │                              │    (打印到日志)              │
 │                              │                              │
 │◄─ 5. 返回成功 ──────────────┤                              │
 │    "验证码已发送"             │                              │
 │                              │                              │
 ├─ 6. 输入验证码               │                              │
 │                              │                              │
 ├─ 7. 提交注册 ──────────────►│                              │
 │    {email, username,         │                              │
 │     password, code}          │                              │
 │                              │                              │
 │                              ├─ 8. 验证验证码 ────────────►│
 │                              │    get(email) == "123456"?   │
 │                              │◄─────────────────────────────┤
 │                              │    成功：删除验证码          │
 │                              │    失败：返回错误            │
 │                              │                              │
 │                              │ 9. 创建用户                  │
 │                              │    - 哈希密码                │
 │                              │    - 保存数据库              │
 │                              │                              │
 │                              │ 10. 生成 Token               │
 │                              │    - access_token            │
 │                              │    - refresh_token           │
 │                              │                              │
 │◄─ 11. 返回 Token ───────────┤                              │
 │                              │                              │
```

---

## 目标接口

### 1. 创建目标

```
POST /api/v1/goals
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "icon": "📚",
  "start_date": "2024-01-01",
  "end_date": "2024-01-30",
  "daily_time_available": "1 小时",
  "experience_level": "零基础",
  "tasks": [
    {
      "day_number": 1,
      "title": "阅读启动",
      "description": "选择第一本书，阅读前 20 页",
      "estimated_minutes": 60
    },
    {
      "day_number": 2,
      "title": "完全休息",
      "description": "让身体恢复",
      "estimated_minutes": 0
    }
  ]
}
```

**字段说明：**
- `tasks`: 每日任务列表（可选），由 AI 生成计划接口返回
- `estimated_minutes`: 预估耗时（分钟），`0` 表示休息日

**响应 (201 Created)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "icon": "📚",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-01-30",
  "duration_days": 30,
  "current_day": 0,
  "progress": 0.0,
  "daily_time_available": "1 小时",
  "experience_level": "零基础",
  "ai_plan": null,
  "today_task": "阅读启动",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**字段说明：**
- `current_day`: 当前打卡天数（0 表示还未开始打卡）
- `today_task`: 当前应该完成的任务（第 current_day + 1 天的任务）
- `progress`: 进度百分比（current_day / duration_days）

**前端职责：**
- 表单验证（日期范围、必填字段）
- 展示 `today_task` 在首页
- 使用 `progress` 绘制进度条

**后端职责：**
- 验证日期范围（结束日期 > 开始日期）
- 计算 `duration_days`
- 保存 `tasks` 到数据库
- 初始化 `current_day = 0`

**错误响应：**
- 400 - 结束日期必须在开始日期之后

---

### 2. 获取目标列表

```
GET /api/v1/goals
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `status` (可选): 按状态过滤 (active, completed, paused, cancelled)
- `skip` (可选): 跳过数量，默认 0
- `limit` (可选): 返回数量，默认 20，最大 100

**响应 (200 OK)：**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "30 天读 5 本书",
      "description": "养成每日阅读习惯",
      "icon": "📚",
      "status": "active",
      "start_date": "2024-01-01",
      "end_date": "2024-01-30",
      "duration_days": 30,
      "current_day": 5,
      "progress": 0.17,
      "daily_time_available": "1 小时",
      "experience_level": "零基础",
      "ai_plan": null,
      "today_task": "第 6 天的任务标题",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

**前端职责：**
- 列表分页加载
- 展示 `today_task`
- 使用 `progress` 绘制进度条

**后端职责：**
- 按 `current_day + 1` 查询 `today_task`
- 计算 `progress`
- 分页查询

---

### 3. 获取单个目标详情

```
GET /api/v1/goals/{goal_id}
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "icon": "📚",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-01-30",
  "duration_days": 30,
  "current_day": 5,
  "progress": 0.17,
  "daily_time_available": "1 小时",
  "experience_level": "零基础",
  "ai_plan": null,
  "today_task": "第 6 天的任务标题",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**前端职责：**
- 展示目标详情
- 展示任务列表

**后端职责：**
- 验证目标所有权
- 返回 `today_task`

**错误响应：**
- 404 - 目标不存在

---

### 4. 更新目标

```
PUT /api/v1/goals/{goal_id}
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体（所有字段可选）：**
```json
{
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "icon": "📚",
  "status": "active",
  "current_day": 10
}
```

**响应 (200 OK)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "icon": "📚",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-01-30",
  "duration_days": 30,
  "current_day": 10,
  "progress": 0.33,
  "daily_time_available": "1 小时",
  "experience_level": "零基础",
  "ai_plan": null,
  "today_task": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**可更新字段：**
- `title`: 目标标题
- `description`: 目标描述
- `icon`: 目标图标
- `status`: 目标状态 (active, completed, paused, cancelled)
- `current_day`: 当前打卡天数（手动调整）

**前端职责：**
- 提供编辑界面
- 验证修改后的数据

**后端职责：**
- 验证目标所有权
- 验证 `status` 枚举值
- 重新计算 `progress`

---

### 5. 删除目标

```
DELETE /api/v1/goals/{goal_id}
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (204 No Content)**

**前端职责：**
- 二次确认
- 从列表移除

**后端职责：**
- 验证目标所有权
- 级联删除 tasks、checkins

**错误响应：**
- 404 - 目标不存在

---

### 6. 获取目标的每日任务列表

```
GET /api/v1/goals/{goal_id}/tasks
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "goal_id": "550e8400-e29b-41d4-a716-446655440001",
    "day_number": 1,
    "title": "阅读启动",
    "description": "选择第一本书，阅读前 20 页",
    "estimated_minutes": 60,
    "status": "pending",
    "completed_at": null,
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "goal_id": "550e8400-e29b-41d4-a716-446655440001",
    "day_number": 2,
    "title": "持续输入",
    "description": "阅读 20-40 页，记录 3 个核心观点",
    "estimated_minutes": 60,
    "status": "pending",
    "completed_at": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**前端职责：**
- 展示任务列表
- 高亮当前任务（`today_task`）

**后端职责：**
- 验证目标所有权
- 按 `day_number` 排序

**错误响应：**
- 404 - 目标不存在

---

### 7. AI 生成目标计划

```
POST /api/v1/goals/plan/generate
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "title": "30 天读 5 本书",
  "description": "养成每日阅读习惯",
  "duration_days": 30,
  "daily_time_available": "1 小时",
  "experience_level": "零基础"
}
```

**响应 (200 OK)：**
```json
{
  "success": true,
  "plan": {
    "weekly_plans": [
      {
        "week_number": 1,
        "title": "建立阅读习惯",
        "description": "适应每日阅读节奏，完成第 1 本书的 50%"
      }
    ],
    "daily_tasks": [
      {
        "day_number": 1,
        "title": "阅读启动",
        "description": "选择第一本书，阅读前 20 页并做关键词标记",
        "estimated_minutes": 60
      },
      {
        "day_number": 2,
        "title": "持续输入",
        "description": "阅读 20-40 页，用便签记录 3 个核心观点",
        "estimated_minutes": 60
      }
    ]
  },
  "reasoning": "### 第 1 步：分析用户和目标\n- 核心难点：克服起床瞬间的惰性\n- 最可能在第 5-7 天放弃：新鲜感消退后遇到第一个周末\n- 前 3 天最小习惯：①固定闹钟位置 ②醒来立即拉开窗帘 ③床头放好晨间第一杯水\n\n### 第 2 步：设计周节奏\n第 1 周：环境改造周 | 第 2 周：流程固化周 | 第 3 周：抗干扰周 | 第 4 周：习惯内化周",
  "error": null
}
```

**字段说明：**
- `reasoning`: AI 的思考过程（Markdown 格式），包含：
  - **目标类型识别**：习惯养成型 / 技能学习型 / 项目完成型 / 健康运动型
  - 对目标核心难点的分析
  - 用户可能放弃的时间点预测
  - 每周设计逻辑和节奏安排
  - 任务设计的自我检查说明

**前置任务设计原则（已内置到 AI）：**

| 目标类型 | 前置任务策略 | 示例 |
|---------|-------------|------|
| **习惯养成型** | 前 1-2 天完成所有环境准备，后面专注练习核心动作 | 早起：第 1 天买闹钟+放远，第 2 天开始实践早起 |
| **技能学习型** | 前 1-2 天安装环境/工具，然后按难度递进学习 | Python：第 1-2 天安装环境，第 3 天开始学变量 |
| **项目完成型** | 前置拆解任务，然后按模块/里程碑推进 | 写书：第 1 周大纲，第 2-4 周写初稿 |
| **健康运动型** | 前置学习动作要领/安全事项，然后强度递进 | 健身：第 1 天学动作，第 2 天开始训练 |

**核心原则：**
- 环境准备类任务应该**集中在前 1-2 天完成**，不要分散到多天
- 真正需要分散的是**难度递进的练习**，而不是准备工作
- 不能为了"填满天数"而把本可一天完成的事硬拆成多天

**前端展示建议：**

1. **展示 `reasoning` 在计划顶部**
   - 用可折叠面板展示 AI 思考过程
   - 帮助用户理解计划背后的逻辑，增加信任感
   - 示例标题："🤖 AI 教练的分析思路"

2. **展示目标类型标签**
   - 在计划顶部显示"这是习惯养成型目标"或"这是技能学习型目标"
   - 帮助用户理解前置任务的设计逻辑

3. **任务描述已优化为可执行格式**
   - 每条任务包含：动作 + 对象 + 完成标准
   - 不再是"早睡"、"早起"等空泛词汇
   - 示例："将手机闹钟放在距离床 2 米外的桌面，设置 8:00 响铃"

4. **周计划可以作为进度分组展示**
   - 每 7 天为一组，显示当周主题
   - 帮助用户理解当前阶段的重点

**前端职责：**
- 展示 AI 计划供用户确认
- 展示 `reasoning` 帮助用户理解计划逻辑
- 展示目标类型标签
- 用户确认后提交创建目标

**后端职责：**
- 调用 AI 服务生成计划（使用思考链方式）
- 解析 AI 返回的 JSON 和 reasoning
- 处理 AI 服务错误

**质量标准（AI 已内置）：**

✅ 好的任务描述：
- "阅读《XXX》第 1-3 章，用便签标记 3 个核心观点，写在笔记里"
- "写 500 字关于 XX 的总结，包含：问题定义、原因分析、解决方案"
- "完成 XX 环境搭建，运行 hello world 示例并截图"

❌ 坏的任务描述（AI 已禁止生成）：
- "早睡"、"早起"、"定闹钟" — 太空泛，没有具体行动
- "了解 XX"、"学习 XX" — 无法衡量是否完成
- "继续努力"、"坚持下去" — 废话，没有指导价值

**实际输出示例：**

**习惯养成型（30 天 8 点起床）：**
```
第 1 天：物理闹钟部署 → 购买机械闹钟放置在距离床 2 米的位置，清空床头所有电子设备
第 2 天：双重闹钟设置 → 手机设置 7:55 和 8:00 两个闹钟，音量调至最大，睡衣叠放在闹钟旁
第 3 天：5 秒启动训练 → 闹钟响后 5 秒内完成坐起动作，双脚落地保持站立 3 秒
```

**技能学习型（30 天学会 Python）：**
```
第 1 天：安装 Python 并运行第一行代码 → 访问 python.org 下载安装，命令行执行 print('Hello World')
第 2 天：安装代码编辑器 → 下载安装 VS Code，创建 hello.py 文件，写下 5 行 print 语句
第 3 天：学习变量 → 定义 3 个变量（姓名、年龄、城市），用 print 打印出来
```

---

## 打卡接口

### 1. 创建打卡记录

```
POST /api/v1/checkins
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "notes": "今天学习了变量和数据类型，感觉还不错！",
  "mood_rating": 4
}
```

**响应 (201 Created)：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "notes": "今天学习了变量和数据类型，感觉还不错！",
  "mood_rating": 4,
  "ai_feedback": "太棒了！你已经连续打卡 5 天了，继续保持！",
  "ai_suggestion": "每天进步一点点，积累就是大改变。",
  "streak_count": 5,
  "created_at": "2024-01-05T10:30:00Z",
  "goal": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "current_day": 5,
    "duration_days": 30,
    "progress": 16.7,
    "today_task": "第 6 天的任务标题"
  }
}
```

**字段说明：**
- `streak_count`: 连续打卡天数
- `ai_feedback`: AI 生成的鼓励性点评
- `ai_suggestion`: AI 生成的改进建议
- `goal`: 更新后的目标信息
  - `id`: 目标 ID
  - `current_day`: 当前打卡天数（打卡后已 +1）
  - `duration_days`: 总天数
  - `progress`: 进度百分比（current_day / duration_days * 100）
  - `today_task`: 下一个任务（第 current_day + 1 天的任务）

**前端职责：**
- 使用 `goal.progress` 更新进度条
- 使用 `goal.today_task` 更新今日任务
- 展示 AI 点评
- 刷新目标列表

**后端职责：**
- 验证今天未打卡
- 计算 `streak_count`
- 调用 AI 生成点评
- 更新 `goal.current_day`
- 计算 `progress`
- 查询 `today_task`

**错误响应：**
- 400 - 今天已经打卡过了
- 404 - 目标不存在

---

### 2. 获取打卡记录列表

```
GET /api/v1/checkins
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `goal_id` (可选): 按目标 ID 过滤
- `skip` (可选): 跳过数量，默认 0
- `limit` (可选): 返回数量，默认 20，最大 100

**响应 (200 OK)：**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "notes": "今天学习了变量和数据类型",
      "mood_rating": 4,
      "ai_feedback": "太棒了！",
      "ai_suggestion": "继续保持！",
      "streak_count": 5,
      "created_at": "2024-01-05T10:30:00Z"
    }
  ],
  "total": 5,
  "current_streak": 5
}
```

**前端职责：**
- 列表分页
- 展示打卡历史

**后端职责：**
- 分页查询
- 计算 `current_streak`

---

### 3. 获取连续打卡天数

```
GET /api/v1/checkins/streak
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `goal_id` (可选): 指定目标的连续打卡天数

**响应 (200 OK)：**
```json
{
  "streak_count": 5
}
```

**前端职责：**
- 展示连续打卡天数

**后端职责：**
- 计算连续打卡天数

---

## 学习伙伴接口

### 1. 获取学习伙伴列表

```
GET /api/v1/partners
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "partner_id": "550e8400-e29b-41d4-a716-446655440001",
    "partner_username": "partner123",
    "partner_avatar_url": null,
    "status": "accepted",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**状态说明：**
- `pending`: 待处理
- `accepted`: 已接受
- `rejected`: 已拒绝

---

### 2. 发送学习伙伴请求

```
POST /api/v1/partners/request
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `partner_username`: 对方用户名

**响应 (200 OK)：**
```json
{
  "message": "已发送学习伙伴请求"
}
```

**错误响应：**
- 404 - 用户不存在
- 400 - 不能添加自己为学习伙伴 / 已经是学习伙伴或已有待处理请求

---

### 3. 获取挑战列表

```
GET /api/v1/partners/challenges
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**查询参数：**
- `status` (可选): 挑战状态 (active, completed, cancelled)，默认 active

**响应 (200 OK)：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "30 天编程挑战",
    "description": "连续 30 天每天写代码",
    "icon": "💪",
    "challenge_type": "streak",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T00:00:00Z",
    "max_participants": 100,
    "current_participants": 45,
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### 4. 加入挑战

```
POST /api/v1/partners/challenges/{challenge_id}/join
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
{
  "message": "已加入挑战"
}
```

**错误响应：**
- 404 - 挑战不存在
- 400 - 挑战不可加入 / 已加入该挑战 / 挑战已满员

---

### 5. 获取挑战参与者列表

```
GET /api/v1/partners/challenges/{challenge_id}/participants
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "username": "user123",
    "avatar_url": null,
    "progress_score": 100,
    "rank": 1,
    "joined_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## 错误处理

### 标准错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

| 状态码 | 说明 | 前端处理 |
|--------|------|----------|
| 400 | 请求参数错误 | 展示错误信息，让用户修改 |
| 401 | 未认证/Token 过期 | 尝试刷新 Token，失败则退出登录 |
| 403 | 无权限 | 提示无权限，引导用户联系管理员 |
| 404 | 资源不存在 | 返回上一页或展示空状态 |
| 500 | 服务器错误 | 稍后重试，展示友好错误页 |

### Token 过期处理流程

```
前端检测 401 ──► 使用 refresh_token 刷新 ──► 成功 ──► 重试原请求
                      │
                      ▼
                   失败 ──► 清除 Token ──► 跳转登录页
```

---

## 数据字典

### 邮箱验证码

| 字段 | 说明 |
|------|------|
| 长度 | 6 位数字 |
| 有效期 | 10 分钟 |
| 存储 | Redis（过期自动删除） |
| 使用 | 验证成功后自动删除，防止重复使用 |

### 验证码邮件配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SMTP_HOST` | SMTP 服务器地址 | - |
| `SMTP_PORT` | SMTP 端口 | 587 |
| `SMTP_TLS` | 是否使用 TLS | true |
| `SMTP_USERNAME` | SMTP 用户名 | - |
| `SMTP_PASSWORD` | SMTP 密码（授权码） | - |
| `SMTP_FROM_EMAIL` | 发件人邮箱 | - |

**注意**: 未配置 SMTP 时，验证码仅打印到日志，不发送邮件。

### 目标状态 (status)

| 值 | 说明 | 前端展示 |
|----|------|----------|
| `active` | 进行中 | 正常显示，可打卡 |
| `completed` | 已完成 | 展示完成状态，不可打卡 |
| `paused` | 已暂停 | 展示暂停状态，不可打卡 |
| `cancelled` | 已取消 | 灰色展示，不可操作 |

### 打卡规则

- 每天只能打卡一次（按 UTC 日期计算）
- 打卡后 `current_day` 自动 +1
- `progress = current_day / duration_days * 100`

### 经验水平 (experience_level)

| 值 | 说明 |
|----|------|
| `零基础` | 完全没有经验 |
| `有一些基础` | 有一定基础 |
| `进阶` | 进阶水平 |

### 每日任务状态

| 值 | 说明 |
|----|------|
| `pending` | 待完成 |
| `completed` | 已完成 |
| `skipped` | 已跳过 |

### 每日任务字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `estimated_minutes` | int | 预估耗时（分钟），`0` 表示休息日 |
| `day_number` | int | 第几天的任务（从 1 开始） |

---

## API 变更日志

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| 2026-04-07 | 1.2 | AI 计划生成优化：使用思考链方式，新增 `reasoning` 字段返回分析过程；新增目标类型识别（习惯养成型/技能学习型/项目完成型/健康运动型）；前置任务优化（环境准备集中在前 1-2 天完成）；任务描述优化为具体可执行格式 |
| 2026-04-03 | 1.1 | 添加邮箱验证码功能：发送验证码接口、验证邮箱接口、注册接口升级 |
| 2026-04-03 | 1.0 | 初始版本，包含认证、目标、打卡、伙伴接口 |
