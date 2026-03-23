from app.core.celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="tasks.add")
def add(x: int, y: int) -> int:
    return x + y
