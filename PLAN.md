# AI Goal Coach Backend - 工程规划审查

## 一、项目概述

**项目名称**: ai-goal-coach-backend
**技术栈**: FastAPI + PostgreSQL
**认证方式**: JWT (JSON Web Token)

---

## 二、数据模型设计

### 2.1 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

**Pydantic 模型**:
```python
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    avatar_url: Optional[str]
    created_at: datetime
```

---

### 2.2 目标表 (goals)

根据前端代码分析，目标包含以下字段：

```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,              -- 如 "30 天读 5 本书"
    description TEXT,                         -- 目标详细描述
    icon VARCHAR(50) DEFAULT '🎯',            -- 目标图标
    status VARCHAR(20) DEFAULT 'active',      -- active, completed, paused, cancelled

    -- 时间相关
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER NOT NULL,           -- 总天数

    -- 进度追踪
    current_day INTEGER DEFAULT 0,            -- 当前第几天

    -- 用户情况
    daily_time_available VARCHAR(50),         -- "30 分钟", "1 小时", "2 小时", "灵活"
    experience_level VARCHAR(20),             -- "零基础", "有一些基础", "中级", "高级"

    -- AI 生成内容
    ai_plan JSONB,                            -- AI 生成的详细计划

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_user_status ON goals(user_id, status);
```

**Pydantic 模型**:
```python
class GoalCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    icon: str = Field(default='🎯', max_length=50)
    start_date: date
    end_date: date
    daily_time_available: str
    experience_level: str

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_day: Optional[int] = None

class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    icon: str
    status: str
    start_date: date
    end_date: date
    duration_days: int
    current_day: int
    progress: float  # 0-1 之间
    ai_plan: Optional[dict]
    created_at: datetime
```

---

### 2.3 每日任务表 (daily_tasks)

```sql
CREATE TABLE daily_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,              -- 第几天
    title VARCHAR(255) NOT NULL,              -- 任务标题
    description TEXT,                         -- 任务详细描述
    estimated_minutes INTEGER,                -- 预计耗时
    status VARCHAR(20) DEFAULT 'pending',     -- pending, completed, skipped
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(goal_id, day_number)
);

-- 索引
CREATE INDEX idx_daily_tasks_goal_id ON daily_tasks(goal_id);
CREATE INDEX idx_daily_tasks_status ON daily_tasks(status);
CREATE INDEX idx_daily_tasks_goal_day ON daily_tasks(goal_id, day_number);
```

---

### 2.4 打卡记录表 (checkins)

```sql
CREATE TABLE checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    task_id UUID REFERENCES daily_tasks(id),

    -- 打卡内容
    notes TEXT,                               -- 用户分享的打卡心得
    mood_rating INTEGER CHECK (mood_rating BETWEEN 1 AND 5),  -- 心情评分

    -- AI 点评
    ai_feedback TEXT,
    ai_suggestion TEXT,

    -- 连续打卡
    streak_count INTEGER DEFAULT 1,           -- 连续打卡天数

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_checkins_user_id ON checkins(user_id);
CREATE INDEX idx_checkins_goal_id ON checkins(goal_id);
CREATE INDEX idx_checkins_created_at ON checkins(created_at);
CREATE INDEX idx_checkins_user_date ON checkins(user_id, created_at);
```

**Pydantic 模型**:
```python
class CheckinCreate(BaseModel):
    goal_id: UUID
    notes: Optional[str] = None
    mood_rating: Optional[int] = Field(None, ge=1, le=5)

class CheckinResponse(BaseModel):
    id: UUID
    goal_id: UUID
    notes: Optional[str]
    mood_rating: Optional[int]
    ai_feedback: Optional[str]
    streak_count: int
    created_at: datetime
```

---

### 2.5 成就表 (achievements) - 预留扩展

```sql
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,    -- "streak_7", "first_goal_completed", etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, achievement_type)
);

CREATE INDEX idx_achievements_user_id ON achievements(user_id);
```

---

## 三、API 接口设计

### 3.1 认证模块 (Authentication)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| POST | `/api/v1/auth/logout` | 用户登出 | ✅ |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | ✅ |
| POST | `/api/v1/auth/refresh` | 刷新 Access Token | ✅ |
| POST | `/api/v1/auth/change-password` | 修改密码 | ✅ |

**请求/响应示例**:

```
POST /api/v1/auth/register
Request:
{
    "email": "user@example.com",
    "username": "张三",
    "password": "securePassword123"
}

Response (201):
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "user": {
        "id": "550e8400-...",
        "email": "user@example.com",
        "username": "张三",
        "created_at": "2026-03-27T10:00:00Z"
    }
}
```

---

### 3.2 目标模块 (Goals)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/goals` | 获取用户所有目标 | ✅ |
| GET | `/api/v1/goals/{goal_id}` | 获取单个目标详情 | ✅ |
| POST | `/api/v1/goals` | 创建新目标 | ✅ |
| PUT | `/api/v1/goals/{goal_id}` | 更新目标 | ✅ |
| PATCH | `/api/v1/goals/{goal_id}/status` | 更新目标状态 | ✅ |
| DELETE | `/api/v1/goals/{goal_id}` | 删除目标 | ✅ |
| GET | `/api/v1/goals/{goal_id}/tasks` | 获取目标的每日任务列表 | ✅ |

**请求/响应示例**:

```
POST /api/v1/goals
Request:
{
    "title": "30 天读 5 本书",
    "description": "每天阅读 40 分钟",
    "icon": "📚",
    "start_date": "2026-03-27",
    "end_date": "2026-04-26",
    "daily_time_available": "1 小时",
    "experience_level": "有一些基础"
}

Response (201):
{
    "id": "550e8400-...",
    "user_id": "660e8400-...",
    "title": "30 天读 5 本书",
    "icon": "📚",
    "status": "active",
    "start_date": "2026-03-27",
    "end_date": "2026-04-26",
    "duration_days": 30,
    "current_day": 0,
    "progress": 0.0,
    "ai_plan": {
        "weekly_plans": [...],
        "daily_tasks": [...]
    },
    "created_at": "2026-03-27T10:00:00Z"
}
```

---

### 3.3 打卡模块 (Checkins)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/checkins` | 创建打卡记录 | ✅ |
| GET | `/api/v1/checkins` | 获取用户打卡历史 | ✅ |
| GET | `/api/v1/goals/{goal_id}/checkins` | 获取指定目标的打卡记录 | ✅ |
| GET | `/api/v1/checkins/streak` | 获取当前连续打卡天数 | ✅ |

**请求/响应示例**:

```
POST /api/v1/checkins
Request:
{
    "goal_id": "550e8400-...",
    "notes": "今天读了 81-100 页，内容很有启发",
    "mood_rating": 4
}

Response (201):
{
    "id": "770e8400-...",
    "goal_id": "550e8400-...",
    "notes": "今天读了 81-100 页，内容很有启发",
    "mood_rating": 4,
    "ai_feedback": "太棒了！你已经连续打卡 7 天了",
    "streak_count": 7,
    "created_at": "2026-03-27T10:00:00Z"
}
```

---

### 3.4 统计模块 (Stats)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/stats/overview` | 获取总体统计 | ✅ |
| GET | `/api/v1/stats/goals/{goal_id}` | 获取指定目标统计 | ✅ |
| GET | `/api/v1/stats/weekly` | 获取周统计数据 | ✅ |

---

## 四、项目目录结构

```
ai-goal-coach-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py         # JWT、密码加密
│   │   └── dependencies.py     # 依赖注入
│   │
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── daily_task.py
│   │   └── checkin.py
│   │
│   ├── schemas/                # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── checkin.py
│   │   └── token.py
│   │
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── goals.py
│   │   │   ├── checkins.py
│   │   │   └── stats.py
│   │   └── deps.py
│   │
│   └── services/               # 业务逻辑
│       ├── __init__.py
│       ├── ai_coach.py         # AI 教练服务 (调用 Claude API)
│       └── stats.py
│
├── alembic/                    # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_goals.py
│   └── test_checkins.py
│
├── .env                        # 环境变量
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 五、环境变量配置

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/ai_goal_coach

# JWT 配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API 配置
API_V1_PREFIX=/api/v1
PROJECT_NAME=AI Goal Coach Backend

# AI 服务 (可选)
ANTHROPIC_API_KEY=sk-ant-...

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

---

## 六、技术选型说明

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 高性能、异步支持、自动文档 |
| ORM | SQLAlchemy 2.0 | 成熟稳定、类型友好 |
| 迁移 | Alembic | SQLAlchemy 官方迁移工具 |
| 认证 | JWT + bcrypt | 无状态、安全 |
| 数据验证 | Pydantic v2 | 与 FastAPI 深度集成 |
| 测试 | pytest + httpx | 异步测试支持 |

---

## 七、决策记录

### 已确认 (2026-03-27)

1. **LLM 集成**: 使用 OpenAI SDK (兼容多厂商)
   - 通过 OpenAI SDK 的 `base_url` 和 `api_key` 配置，可灵活切换不同厂商
   - 支持 Anthropic/Claude、DeepSeek、Moonshot 等兼容 OpenAI API 的服务

2. **学习伙伴功能**: 需要实现
   - 组队 PK 功能
   - 用户匹配/排行榜

3. **付费会员**: 暂不实现

4. **开发范围**: Phase 1 MVP + AI 集成功能

---

## 八、开发状态

**Phase 1 - MVP (已完成)**:
- [x] 用户注册/登录 (JWT)
- [x] 目标 CRUD
- [x] 每日任务生成
- [x] 打卡功能

**Phase 2 - 增强 (已完成)**:
- [x] AI 生成计划集成 (OpenAI SDK)
- [x] AI 打卡点评
- [x] 统计面板
- [x] 学习伙伴/组队 PK

**Phase 3 - 扩展 (待实现)**:
- [ ] 推送通知
- [ ] 会员订阅

---

请确认以上设计是否符合需求，确认后我将开始编写代码。
