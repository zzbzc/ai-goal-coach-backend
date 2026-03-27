"""目标和每日任务模型"""
import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Date, ForeignKey,
    Boolean, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Goal(Base):
    """目标表"""
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="🎯")
    status = Column(String(20), default="active")  # active, completed, paused, cancelled

    # 时间相关
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    duration_days = Column(Integer, nullable=False)

    # 进度追踪
    current_day = Column(Integer, default=0)

    # 用户情况
    daily_time_available = Column(String(50))  # "30 分钟", "1 小时", etc.
    experience_level = Column(String(20))  # "零基础", "有一些基础", etc.

    # AI 生成内容
    ai_plan = Column(JSONB, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    tasks = relationship("DailyTask", back_populates="goal", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_goals_user_id", "user_id"),
        Index("idx_goals_status", "status"),
        Index("idx_goals_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<Goal {self.title}>"

    @property
    def progress(self) -> float:
        """计算进度百分比"""
        if self.duration_days == 0:
            return 0.0
        return round(self.current_day / self.duration_days, 2)


class DailyTask(Base):
    """每日任务表"""
    __tablename__ = "daily_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)  # 第几天
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, skipped
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    goal = relationship("Goal", back_populates="tasks")

    __table_args__ = (
        UniqueConstraint("goal_id", "day_number", name="uq_goal_day"),
        Index("idx_daily_tasks_goal_id", "goal_id"),
        Index("idx_daily_tasks_status", "status"),
    )

    def __repr__(self):
        return f"<DailyTask Day {self.day_number}>"
