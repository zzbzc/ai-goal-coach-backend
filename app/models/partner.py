"""学习伙伴模型"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, ForeignKey, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Partner(Base):
    """学习伙伴表"""
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    partner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_partners_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<Partner {self.user_id} -> {self.partner_user_id}>"


class Challenge(Base):
    """组队 PK 挑战表"""
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="🎯")

    # 挑战类型
    challenge_type = Column(String(50), default="streak")  # streak, completion, speed

    # 时间范围
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # 参与人数限制
    max_participants = Column(Integer, default=100)

    # 状态
    status = Column(String(20), default="active")  # active, completed, cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_challenges_status", "status"),
        Index("idx_challenges_dates", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<Challenge {self.name}>"


class ChallengeParticipant(Base):
    """挑战参与者表"""
    __tablename__ = "challenge_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), nullable=True)

    # 进度统计
    progress_score = Column(Integer, default=0)  # 进度分数
    rank = Column(Integer, nullable=True)  # 排名

    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_challenge_participants_challenge", "challenge_id"),
        Index("idx_challenge_participants_user", "user_id"),
    )

    def __repr__(self):
        return f"<ChallengeParticipant {self.user_id} in {self.challenge_id}>"
