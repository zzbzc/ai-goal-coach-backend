"""学习伙伴相关 Schemas"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class PartnerResponse(BaseModel):
    """学习伙伴响应"""
    id: UUID
    partner_id: UUID
    partner_username: str
    partner_avatar_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChallengeResponse(BaseModel):
    """挑战响应"""
    id: UUID
    name: str
    description: Optional[str] = None
    icon: str
    challenge_type: str
    start_date: datetime
    end_date: datetime
    max_participants: int
    current_participants: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChallengeParticipantResponse(BaseModel):
    """挑战参与者响应"""
    id: UUID
    user_id: UUID
    username: str
    avatar_url: Optional[str] = None
    progress_score: int
    rank: Optional[int] = None
    joined_at: datetime

    class Config:
        from_attributes = True


class ChallengeCreate(BaseModel):
    """创建挑战请求"""
    name: str
    description: Optional[str] = None
    icon: str = "🎯"
    challenge_type: str = "streak"
    start_date: datetime
    end_date: datetime
    max_participants: int = 100
