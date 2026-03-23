from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.auth import router as auth_router
from app.api.v1.markets import router as markets_router
from app.api.v1.trades import router as trades_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(
    markets_router,
    prefix="/markets",
    tags=["markets"],
    dependencies=[Depends(get_current_user)],
)
router.include_router(
    trades_router,
    prefix="/trades",
    tags=["trades"],
    dependencies=[Depends(get_current_user)],
)
