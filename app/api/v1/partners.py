"""学习伙伴路由"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.partner import Partner, Challenge, ChallengeParticipant
from app.schemas.partner import (
    PartnerResponse, ChallengeResponse, ChallengeParticipantResponse
)
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/partners", response_model=List[PartnerResponse])
def get_partners(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的学习伙伴"""
    partners = db.query(Partner).filter(
        (Partner.user_id == current_user.id) | (Partner.partner_user_id == current_user.id)
    ).all()

    result = []
    for p in partners:
        partner_user_id = p.partner_user_id if p.user_id == current_user.id else p.user_id
        partner_user = db.query(User).filter(User.id == partner_user_id).first()
        if partner_user:
            result.append({
                "id": p.id,
                "partner_id": partner_user.id,
                "partner_username": partner_user.username,
                "partner_avatar_url": partner_user.avatar_url,
                "status": p.status,
                "created_at": p.created_at,
            })

    return result


@router.post("/partners/request")
def send_partner_request(
    partner_username: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送学习伙伴请求"""
    partner = db.query(User).filter(User.username == partner_username).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if partner.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能添加自己为学习伙伴"
        )

    # 检查是否已经是伙伴
    existing = db.query(Partner).filter(
        ((Partner.user_id == current_user.id) & (Partner.partner_user_id == partner.id)) |
        ((Partner.user_id == partner.id) & (Partner.partner_user_id == current_user.id))
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经是学习伙伴或已有待处理请求"
        )

    partner_request = Partner(
        user_id=current_user.id,
        partner_user_id=partner.id,
        status="pending",
    )
    db.add(partner_request)
    db.commit()

    return {"message": "已发送学习伙伴请求"}


@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(
    status_filter: str = Query("active"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取挑战列表"""
    query = db.query(Challenge)
    if status_filter:
        query = query.filter(Challenge.status == status_filter)

    challenges = query.order_by(Challenge.start_date.desc()).all()

    result = []
    for challenge in challenges:
        participant_count = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge.id
        ).count()

        result.append({
            "id": challenge.id,
            "name": challenge.name,
            "description": challenge.description,
            "icon": challenge.icon,
            "challenge_type": challenge.challenge_type,
            "start_date": challenge.start_date,
            "end_date": challenge.end_date,
            "max_participants": challenge.max_participants,
            "current_participants": participant_count,
            "status": challenge.status,
            "created_at": challenge.created_at,
        })

    return result


@router.post("/challenges/{challenge_id}/join")
def join_challenge(
    challenge_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """加入挑战"""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="挑战不存在"
        )

    if challenge.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="挑战不可加入"
        )

    # 检查是否已加入
    existing = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已加入该挑战"
        )

    # 检查人数限制
    current_count = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id
    ).count()

    if current_count >= challenge.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="挑战已满员"
        )

    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=current_user.id,
    )
    db.add(participant)
    db.commit()

    return {"message": "已加入挑战"}


@router.get("/challenges/{challenge_id}/participants", response_model=List[ChallengeParticipantResponse])
def get_challenge_participants(
    challenge_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取挑战参与者列表"""
    participants = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id
    ).order_by(ChallengeParticipant.rank).all()

    result = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            result.append({
                "id": p.id,
                "user_id": p.user_id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "progress_score": p.progress_score,
                "rank": p.rank,
                "joined_at": p.joined_at,
            })

    return result
