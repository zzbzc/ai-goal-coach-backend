"""API v1 路由器"""
from fastapi import APIRouter
from .auth import router as auth_router
from .goals import router as goals_router
from .checkins import router as checkins_router
from .partners import router as partners_router

api_router = APIRouter(redirect_slashes=False)

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(goals_router, prefix="/goals", tags=["目标"])
api_router.include_router(checkins_router, prefix="/checkins", tags=["打卡"])
api_router.include_router(partners_router, prefix="/partners", tags=["学习伙伴"])

__all__ = ["api_router"]
