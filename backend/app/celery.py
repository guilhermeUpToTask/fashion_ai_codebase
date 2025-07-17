from celery import Celery
from core.config import settings

#celery wil be configured to use redis for both broker and backend
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"] # this path must be correct
)

#Improve configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content =['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)