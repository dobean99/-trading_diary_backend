from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.redis_client import close_redis

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_prefix)


def roots():
    return {"message": "Welcome to FastAPI Modular Example!"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_redis()
