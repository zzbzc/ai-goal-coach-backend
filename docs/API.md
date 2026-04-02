# API 接口文档

AI Goal Coach Backend API 接口文档

**基础信息：**
- **基础路径**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

---

## 目录

1. [认证接口](#认证接口)
2. [目标接口](#目标接口)
3. [打卡接口](#打卡接口)
4. [学习伙伴接口](#学习伙伴接口)

---

## 认证接口

### 1. 用户注册

```
POST /api/v1/auth/register
```

**请求体：**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

**响应 (201 Created)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 2. 用户登录

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
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 3. 刷新 Token

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
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 4. 获取当前用户信息

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
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "avatar_url": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 5. 用户登出

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
  "title": "学习 Python",
  "description": "从零开始学习 Python 编程",
  "icon": "🐍",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "daily_time_available": "1-2 小时",
  "experience_level": "beginner"
}
```

**响应 (201 Created)：**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "学习 Python",
  "description": "从零开始学习 Python 编程",
  "icon": "🐍",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "duration_days": 90,
  "current_day": 0,
  "progress": 0.0,
  "daily_time_available": "1-2 小时",
  "experience_level": "beginner",
  "ai_plan": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

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
      "id": "uuid",
      "user_id": "uuid",
      "title": "学习 Python",
      "description": "从零开始学习 Python 编程",
      "icon": "🐍",
      "status": "active",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "duration_days": 90,
      "current_day": 5,
      "progress": 5.56,
      "daily_time_available": "1-2 小时",
      "experience_level": "beginner",
      "ai_plan": null,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

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
  "id": "uuid",
  "user_id": "uuid",
  "title": "学习 Python",
  "description": "从零开始学习 Python 编程",
  "icon": "🐍",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "duration_days": 90,
  "current_day": 5,
  "progress": 5.56,
  "daily_time_available": "1-2 小时",
  "experience_level": "beginner",
  "ai_plan": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 4. 更新目标

```
PUT /api/v1/goals/{goal_id}
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "title": "学习 Python 编程",
  "description": "系统学习 Python 编程",
  "status": "active",
  "current_day": 10
}
```

**响应 (200 OK)：**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "学习 Python 编程",
  "description": "系统学习 Python 编程",
  "icon": "🐍",
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "duration_days": 90,
  "current_day": 10,
  "progress": 11.11,
  "daily_time_available": "1-2 小时",
  "experience_level": "beginner",
  "ai_plan": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

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
    "id": "uuid",
    "goal_id": "uuid",
    "day_number": 1,
    "title": "安装 Python 环境",
    "description": "下载并安装 Python 3.11",
    "estimated_minutes": 30,
    "status": "pending",
    "completed_at": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

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
  "title": "学习 Python",
  "description": "从零开始学习 Python 编程",
  "duration_days": 30,
  "daily_time_available": "1-2 小时",
  "experience_level": "beginner"
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
        "title": "基础语法入门",
        "description": "学习 Python 基础语法、变量、数据类型"
      }
    ],
    "daily_tasks": [
      {
        "day_number": 1,
        "title": "安装 Python 环境",
        "description": "下载并安装 Python 3.11",
        "estimated_minutes": 30
      }
    ]
  }
}
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
  "goal_id": "uuid",
  "notes": "今天学习了变量和数据类型，感觉还不错！",
  "mood_rating": 4
}
```

**响应 (201 Created)：**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "goal_id": "uuid",
  "notes": "今天学习了变量和数据类型，感觉还不错！",
  "mood_rating": 4,
  "ai_feedback": "太棒了！继续保持这个学习节奏！",
  "ai_suggestion": "明天可以尝试做一些简单的练习题巩固知识。",
  "streak_count": 5,
  "created_at": "2024-01-05T10:30:00Z"
}
```

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
      "id": "uuid",
      "user_id": "uuid",
      "goal_id": "uuid",
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

---

## 学习伙伴接口

### 1. 获取学习伙伴列表

```
GET /api/v1/partners/partners
```

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 (200 OK)：**
```json
[
  {
    "id": "uuid",
    "partner_id": "uuid",
    "partner_username": "partner123",
    "partner_avatar_url": null,
    "status": "accepted",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### 2. 发送学习伙伴请求

```
POST /api/v1/partners/partners/request
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
    "id": "uuid",
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
    "id": "uuid",
    "user_id": "uuid",
    "username": "user123",
    "avatar_url": null,
    "progress_score": 100,
    "rank": 1,
    "joined_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## 错误响应

**400 Bad Request**
```json
{
  "detail": "错误描述信息"
}
```

**401 Unauthorized**
```json
{
  "detail": "邮箱或密码错误"
}
```

**403 Forbidden**
```json
{
  "detail": "没有权限执行此操作"
}
```

**404 Not Found**
```json
{
  "detail": "目标不存在"
}
```

**500 Internal Server Error**
```json
{
  "detail": "服务器内部错误"
}
```

---

## 认证说明

所有需要认证的接口都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 过期后，可以使用 `refresh_token` 调用 `/api/v1/auth/refresh` 接口刷新 Token。
