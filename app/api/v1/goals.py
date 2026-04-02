"""目标路由"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal, DailyTask
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalResponse, GoalListResponse,
    DailyTaskCreate, DailyTaskResponse, PlanGenerateRequest, PlanGenerateResponse
)
from app.api.deps import get_current_user
from app.services.ai_coach import generate_goal_plan

router = APIRouter()


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新目标"""
    # 计算持续天数
    duration_days = (goal_in.end_date - goal_in.start_date).days + 1
    if duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="结束日期必须在开始日期之后"
        )

    goal = Goal(
        user_id=current_user.id,
        title=goal_in.title,
        description=goal_in.description,
        icon=goal_in.icon,
        start_date=goal_in.start_date,
        end_date=goal_in.end_date,
        duration_days=duration_days,
        daily_time_available=goal_in.daily_time_available,
        experience_level=goal_in.experience_level,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    # 保存每日任务（如果有）
    if goal_in.tasks:
        for task_in in goal_in.tasks:
            task = DailyTask(
                goal_id=goal.id,
                day_number=task_in.day_number,
                title=task_in.title,
                description=task_in.description,
                estimated_minutes=task_in.estimated_minutes,
            )
            db.add(task)
        db.commit()

    return goal


@router.get("", response_model=GoalListResponse)
def get_goals(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的目标列表"""
    query = db.query(Goal).filter(Goal.user_id == current_user.id)

    if status_filter:
        query = query.filter(Goal.status == status_filter)

    total = query.count()
    goals = query.order_by(Goal.created_at.desc()).offset(skip).limit(limit).all()

    return GoalListResponse(items=goals, total=total)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个目标详情"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在"
        )

    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: UUID,
    goal_in: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新目标"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在"
        )

    # 更新字段
    update_data = goal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    db.commit()
    db.refresh(goal)

    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除目标"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在"
        )

    db.delete(goal)
    db.commit()

    return None


@router.get("/{goal_id}/tasks", response_model=list[DailyTaskResponse])
def get_goal_tasks(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取目标的每日任务列表"""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在"
        )

    tasks = db.query(DailyTask).filter(
        DailyTask.goal_id == goal_id
    ).order_by(DailyTask.day_number).all()

    return tasks


@router.post("/plan/generate", response_model=PlanGenerateResponse)
async def generate_plan(
    plan_in: PlanGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """AI 生成目标计划"""
    result = await generate_goal_plan(
        title=plan_in.title,
        description=plan_in.description,
        duration_days=plan_in.duration_days,
        daily_time_available=plan_in.daily_time_available,
        experience_level=plan_in.experience_level,
    )

    return result
