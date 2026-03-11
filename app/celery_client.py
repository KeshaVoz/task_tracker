from typing import Optional
from celery import Celery
from celery.schedules import crontab
from app.config import settings

_celery_client: Optional[Celery] = None

def get_celery_client() -> Celery:
    global _celery_client
    if _celery_client is None:
        _celery_client = Celery(
            'task_tracker',
            broker=f'amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@rabbitmq:5672//',
            include=['app.tasks.email']
        )
        
        _celery_client.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Europe/Moscow',
            broker_connection_retry_on_startup=True,
            beat_schedule={
                'send-daily-reports': {
                    'task': 'app.tasks.email.send_daily_report',
                    'schedule': crontab(hour=0, minute=0),
                },
            },
        )
    
    return _celery_client

celery_client = get_celery_client()
