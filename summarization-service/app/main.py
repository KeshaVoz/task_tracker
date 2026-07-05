import logging
from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage
from app.config import settings
from app.schemas import SSummaryReportRequest, SSummaryReportResponse, SClearCacheCommand 
from app.services import summarizer


logger = logging.getLogger("summarization-service.main")


broker = KafkaBroker(settings.KAFKA_URL)
app = FastStream(broker)


@broker.subscriber("summary_requests")
@broker.publisher("summary_responses")
async def handle_summarization(data: SSummaryReportRequest, msg: KafkaMessage) -> SSummaryReportResponse:
    logger.info("Received a new summary request via Kafka for user: %s", data.user_email)
    
    headers = dict(msg.headers or [])
    raw_correlation_id = headers.get("correlation_id", b"unknown-rpc-fallback")
    correlation_id = raw_correlation_id.decode("utf-8") if isinstance(raw_correlation_id, bytes) else str(raw_correlation_id)

    try:
        report_text = await summarizer.generate_summary(data, correlation_id)
    except Exception as e:
        logger.error("Error during LLM generation for user %s: %s", data.user_email, e, exc_info=True)
        await broker.publish(
            value={"error": str(e), "original_payload": data.model_dump()},
            topic="summary_requests.dlq"
        )
        raise e
    
    logger.info("Sending validated RPC response to Kafka.")
    
    return SSummaryReportResponse(
        report_text=report_text,
        correlation_id=correlation_id,
        user_email=data.user_email,
        target_date=data.target_date,
        user_id=data.user_id
    )


@broker.subscriber("system_commands")
async def handle_system_commands(data: SClearCacheCommand, msg: KafkaMessage) -> None:
    headers = dict(msg.headers or [])
    raw_command_type = headers.get("command_type", b"unknown")
    command_type = raw_command_type.decode("utf-8") if isinstance(raw_command_type, bytes) else str(raw_command_type)

    if command_type == "clear_cache":
        logger.info("Received system command to clear AI cache older than %s days.", data.retention_days)
        try:
            deleted_rows = await summarizer.clear_old_cache(days=data.retention_days)
            logger.info("System cleanup complete. Removed %s expired entries from DB.", deleted_rows)
        except Exception as e:
            logger.error("Failed to execute clear_cache command: %s", e, exc_info=True)
