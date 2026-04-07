"""打卡相关 Schemas"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class CheckinCreate(BaseModel):
    """创建打卡请求"""
    goal_id: UUID
    notes: Optional[str] = None
    mood_rating: Optional[int] = Field(None, ge=1, le=5)


class CheckinUpdate(BaseModel):
    """更新打卡请求"""
    notes: Optional[str] = None
    mood_rating: Optional[int] = Field(None, ge=1, le=5)


class CheckinResponse(BaseModel):
    """打卡响应"""
    id: UUID
    user_id: UUID
    goal_id: UUID
    notes: Optional[str] = None
    mood_rating: Optional[int] = None
    ai_feedback: Optional[str] = None
    ai_suggestion: Optional[str] = None
    streak_count: int
    created_at: datetime
    goal: Optional[dict] = None  # 更新后的目标信息

    class Config:
        # 禁用 from_attributes，因为我们手动构建响应
        from_attributes = False


class CheckinListResponse(BaseModel):
    """打卡列表响应"""
    items: List[CheckinResponse]
    total: int
    current_streak: int
