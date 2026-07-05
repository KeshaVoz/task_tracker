from celery import Celery
from celery.schedules import crontab
from app.config import settings


celery_client = Celery("task_tracker", broker=settings.CELERY_BROKER_URL)


celery_client.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1, 
    beat_schedule={
        "send-daily-reports": {
            "task": "app.tasks.email.send_daily_report",
            "schedule": crontab(hour=0, minute=0),
        },
        "clear-old-ai-cache": {
            "task": "app.tasks.email.clear_old_ai_cache_task",
            "schedule": crontab(hour=3, minute=0, day_of_week=0), 
        },
    },
)

celery_client.autodiscover_tasks(['app.tasks'], related_name='email')