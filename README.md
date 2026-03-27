# AI Goal Coach Backend

AI 目标教练的后端 API，基于 FastAPI + PostgreSQL。

## 功能特性

- ✅ 用户注册/登录（JWT 认证）
- ✅ 目标 CRUD（创建、查看、修改、删除）
- ✅ 每日打卡（关联目标）
- ✅ AI 生成计划（OpenAI 兼容）
- ✅ AI 打卡点评
- ✅ 学习伙伴/组队 PK

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT + bcrypt
- **AI 服务**: OpenAI SDK（兼容多厂商）

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 API 密钥
```

### 3. 启动数据库

```bash
# 使用 Docker 启动 PostgreSQL
docker run -d \
  --name ai-goal-coach-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_goal_coach \
  -p 5432:5432 \
  postgres:15
```

### 4. 运行应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 端点

### 认证
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/refresh` - 刷新 Token

### 目标
- `GET /api/v1/goals` - 获取目标列表
- `POST /api/v1/goals` - 创建目标
- `GET /api/v1/goals/{id}` - 获取目标详情
- `PUT /api/v1/goals/{id}` - 更新目标
- `DELETE /api/v1/goals/{id}` - 删除目标

### 打卡
- `POST /api/v1/checkins` - 创建打卡
- `GET /api/v1/checkins` - 获取打卡记录
- `GET /api/v1/checkins/streak` - 获取连续打卡天数

### 学习伙伴
- `GET /api/v1/partners/partners` - 获取学习伙伴
- `POST /api/v1/partners/partners/request` - 发送伙伴请求
- `GET /api/v1/partners/challenges` - 获取挑战列表
- `POST /api/v1/partners/challenges/{id}/join` - 加入挑战

## 项目结构

```
ai-goal-coach-backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── goals.py
│   │   │   ├── checkins.py
│   │   │   ├── partners.py
│   │   │   └── router.py
│   │   └── deps.py
│   ├── core/
│   │   ├── security.py
│   │   └── config.py
│   ├── models/
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── checkin.py
│   │   └── partner.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── checkin.py
│   │   └── partner.py
│   ├── services/
│   │   └── ai_coach.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 开发

### 运行测试

```bash
pytest
```

## 许可证

MIT
