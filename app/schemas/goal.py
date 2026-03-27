"""目标相关 Schemas"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    """创建目标请求"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: str = Field(default="🎯", max_length=50)
    start_date: date
    end_date: date
    daily_time_available: str = Field(..., description="每天可用时间")
    experience_level: str = Field(..., description="经验水平")


class GoalUpdate(BaseModel):
    """更新目标请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|paused|cancelled)$")
    current_day: Optional[int] = Field(None, ge=0)


class GoalResponse(BaseModel):
    """目标响应"""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    icon: str
    status: str
    start_date: date
    end_date: date
    duration_days: int
    current_day: int
    progress: float
    daily_time_available: Optional[str] = None
    experience_level: Optional[str] = None
    ai_plan: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GoalListResponse(BaseModel):
    """目标列表响应"""
    items: List[GoalResponse]
    total: int


class DailyTaskCreate(BaseModel):
    """创建每日任务请求"""
    day_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    estimated_minutes: Optional[int] = Field(None, ge=1)


class DailyTaskUpdate(BaseModel):
    """更新每日任务请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|completed|skipped)$")
    estimated_minutes: Optional[int] = None


class DailyTaskResponse(BaseModel):
    """每日任务响应"""
    id: UUID
    goal_id: UUID
    day_number: int
    title: str
    description: Optional[str] = None
    estimated_minutes: Optional[int] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
