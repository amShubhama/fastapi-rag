from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "document_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    },
)

celery_app.autodiscover_tasks(["src.ingestion"])
