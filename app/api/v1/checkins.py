"""打卡路由"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal, DailyTask
from app.models.checkin import Checkin
from app.schemas.checkin import (
    CheckinCreate, CheckinResponse, CheckinListResponse
)
from app.api.deps import get_current_user
from app.services.ai_coach import generate_checkin_feedback

router = APIRouter()


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin_in: CheckinCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建打卡记录"""
    # 验证目标存在且属于当前用户
    goal = db.query(Goal).filter(
        Goal.id == checkin_in.goal_id,
        Goal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在"
        )

    # 检查今天是否已经打卡
    today = datetime.utcnow().date()
    existing_checkin = db.query(Checkin).filter(
        Checkin.user_id == current_user.id,
        Checkin.goal_id == checkin_in.goal_id,
        Checkin.created_at >= datetime.combine(today, datetime.min.time())
    ).first()

    if existing_checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今天已经打卡过了"
        )

    # 计算连续打卡天数
    streak_count = calculate_streak(current_user.id, checkin_in.goal_id, db) + 1

    # 生成 AI 点评
    ai_feedback = None
    ai_suggestion = None
    if checkin_in.notes:
        try:
            feedback = await generate_checkin_feedback(
                notes=checkin_in.notes,
                streak_count=streak_count,
                goal_title=goal.title
            )
            ai_feedback = feedback.get("feedback")
            ai_suggestion = feedback.get("suggestion")
        except Exception:
            # AI 服务失败不影响打卡
            pass

    checkin = Checkin(
        user_id=current_user.id,
        goal_id=checkin_in.goal_id,
        notes=checkin_in.notes,
        mood_rating=checkin_in.mood_rating,
        ai_feedback=ai_feedback,
        ai_suggestion=ai_suggestion,
        streak_count=streak_count,
    )
    db.add(checkin)

    # 更新目标进度
    goal.current_day = min(goal.current_day + 1, goal.duration_days)
    db.commit()
    db.refresh(checkin)

    # 获取更新后的 today_task（current_day + 1，因为 current_day=1 时应该显示第 2 天的任务）
    today_task = db.query(DailyTask).filter(
        DailyTask.goal_id == goal.id,
        DailyTask.day_number == goal.current_day + 1
    ).first()

    # 计算进度百分比
    progress = round(goal.current_day / goal.duration_days * 100, 1) if goal.duration_days > 0 else 0.0

    # 构建目标信息
    goal_data = {
        "id": str(goal.id),
        "current_day": goal.current_day,
        "duration_days": goal.duration_days,
        "progress": progress,
        "today_task": today_task.title if today_task else None,
    }

    # 构建响应数据
    return CheckinResponse(
        id=checkin.id,
        user_id=checkin.user_id,
        goal_id=checkin.goal_id,
        notes=checkin.notes,
        mood_rating=checkin.mood_rating,
        ai_feedback=checkin.ai_feedback,
        ai_suggestion=checkin.ai_suggestion,
        streak_count=checkin.streak_count,
        created_at=checkin.created_at,
        goal=goal_data,
    )


@router.get("", response_model=CheckinListResponse)
def get_checkins(
    goal_id: UUID = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取打卡记录"""
    query = db.query(Checkin).filter(Checkin.user_id == current_user.id)

    if goal_id:
        # 验证目标属于当前用户
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user.id
        ).first()
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标不存在"
            )
        query = query.filter(Checkin.goal_id == goal_id)

    total = query.count()
    checkins = query.order_by(Checkin.created_at.desc()).offset(skip).limit(limit).all()

    # 获取当前连续打卡天数
    current_streak = get_current_streak(current_user.id, goal_id if goal_id else None, db)

    # 手动构建 CheckinResponse 列表
    items = []
    for checkin in checkins:
        items.append({
            "id": checkin.id,
            "user_id": checkin.user_id,
            "goal_id": checkin.goal_id,
            "notes": checkin.notes,
            "mood_rating": checkin.mood_rating,
            "ai_feedback": checkin.ai_feedback,
            "ai_suggestion": checkin.ai_suggestion,
            "streak_count": checkin.streak_count,
            "created_at": checkin.created_at,
            "goal": None,  # 列表接口不包含完整 goal 信息
        })

    return CheckinListResponse(
        items=items,
        total=total,
        current_streak=current_streak
    )


@router.get("/streak")
def get_streak_count(
    goal_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取连续打卡天数"""
    streak = get_current_streak(current_user.id, goal_id, db)
    return {"streak_count": streak}


def calculate_streak(user_id: UUID, goal_id: UUID, db: Session) -> int:
    """计算连续打卡天数"""
    checkins = db.query(Checkin).filter(
        Checkin.user_id == user_id,
        Checkin.goal_id == goal_id
    ).order_by(Checkin.created_at.desc()).limit(30).all()

    if not checkins:
        return 0

    from datetime import timedelta, date
    today = date.today()
    streak = 0

    for checkin in checkins:
        checkin_date = checkin.created_at.date()
        days_diff = (today - checkin_date).days

        # 如果是今天或昨天，继续计算
        if days_diff <= streak:
            streak += 1
        else:
            break

    return streak


def get_current_streak(user_id: UUID, goal_id: UUID, db: Session) -> int:
    """获取当前连续打卡天数"""
    return calculate_streak(user_id, goal_id, db)
