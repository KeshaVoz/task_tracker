import logging
import json
from kafka import KafkaProducer
from datetime import datetime, timedelta, timezone
from celery import current_task
from celery.signals import worker_process_init
from app.celery_client import celery_client
from app.dao.users import UserDAO
from app.schemas.email import SSummaryReportRequest
from app.services.tasks import TaskService
from app.services.email import EmailService
from app.config import settings


logger = logging.getLogger(__name__)


kafka_producer = None


@worker_process_init.connect
def init_worker_kafka(**kwargs) -> None:
    global kafka_producer

    logger.info("Initializing isolated KafkaProducer for worker process...")
    kafka_producer = KafkaProducer(
        bootstrap_servers=getattr(settings, "KAFKA_URL", "kafka:29092"),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        compression_type='gzip',
        request_timeout_ms=5000,
        max_block_ms=5000
    )


@celery_client.task(
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    default_retry_delay=60
)
def process_user_report(user_id: int) -> None:
    user = UserDAO.find_one_or_none_sync(id=user_id)
    if not user:
        logger.warning("User with id %s not found. Skipping report.", user_id)
        return


    beat_time_raw = getattr(current_task.request, "time_start", None)
    if beat_time_raw and isinstance(beat_time_raw, datetime):
        beat_time = beat_time_raw
    else:
        beat_time = datetime.now(timezone.utc)    

    stable_time = beat_time - timedelta(hours=1)
    target_date = stable_time.date()
    correlation_id = f"report-{user_id}-{target_date}"

    logger.info("Sending request to Kafka for user %s (date: %s)", user.email, target_date)
    
    analytics = TaskService.get_user_daily_analytics(user_id, target_date)
    
    if analytics.total_pending == 0 and analytics.completed_count == 0:
        logger.info(
            "User %s has 0 pending and 0 completed tasks for %s. Skipping Kafka RPC request.", 
            user.email, target_date
        )
        return
    
    logger.info("Sending request to Kafka for user %s (date: %s)", user.email, target_date)

    rpc_request = SSummaryReportRequest(
        total_pending=analytics.total_pending,
        pending_titles=analytics.pending_titles,
        completed_count=analytics.completed_count,
        completed_titles=analytics.completed_titles,
        user_email=user.email,
        target_date=str(target_date),
        user_id=user.id
    )
    
    headers = [("correlation_id", correlation_id.encode("utf-8"))]
    
    kafka_producer.send(
        "summary_requests", 
        value=rpc_request.model_dump(), 
        headers=headers
    )
    kafka_producer.flush()
    
    logger.info("RPC Request sent to Kafka for user %s.", user.email)


@celery_client.task
def send_daily_report() -> None:
    CHUNK_SIZE = 500
    offset = 0
    while True:
        user_ids = UserDAO.find_all_ids_chunk(limit=CHUNK_SIZE, offset=offset)
        if not user_ids: break
        for user_id in user_ids:
            process_user_report.delay(user_id)
        offset += CHUNK_SIZE


@celery_client.task
def send_welcome_email(email: str) -> bool:
    logger.info("Triggering welcome email delivery to %s via EmailService", email)
    try:
        EmailService.send_welcome_email(user_email=email)
        logger.info("Welcome email successfully sent to %s", email)
        return True
    except Exception as e:
        logger.error("Failed to process welcome email for %s: %s", email, e)
        return False
    

@celery_client.task
def clear_old_ai_cache_task() -> None:
    logger.info("Sending system command to Kafka to clear old AI cache...")
    try:
        command_payload = {"retention_days": 30}

        kafka_producer.send(
            topic="system_commands", 
            value=command_payload,
            headers=[("command_type", b"clear_cache")]
        )
        kafka_producer.flush()
        logger.info("System command 'clear_cache' successfully sent to Kafka.")
    except Exception as e:
        logger.error("Failed to send clear_cache command to Kafka: %s", e, exc_info=True)

