from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.trades import router as trades_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(trades_router, prefix="/trades", tags=["trades"])
