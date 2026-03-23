from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "trading_diary",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    timezone="UTC",
)

celery_app.autodiscover_tasks(["app.services"])
