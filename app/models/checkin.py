"""打卡记录模型"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Checkin(Base):
    """打卡记录表"""
    __tablename__ = "checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=True)

    # 打卡内容
    notes = Column(Text, nullable=True)  # 用户分享的打卡心得
    mood_rating = Column(Integer, nullable=True)  # 心情评分 1-5

    # AI 点评
    ai_feedback = Column(Text, nullable=True)
    ai_suggestion = Column(Text, nullable=True)

    # 连续打卡
    streak_count = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    goal = relationship("Goal", back_populates="checkins")

    __table_args__ = (
        CheckConstraint("mood_rating >= 1 AND mood_rating <= 5", name="check_mood_rating"),
        Index("idx_checkins_user_id", "user_id"),
        Index("idx_checkins_goal_id", "goal_id"),
        Index("idx_checkins_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Checkin {self.id}>"
