import os
import sys
import json
import logging
from datetime import datetime
import time


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
sys.path.append(PROJECT_ROOT)


from kafka import KafkaConsumer
from app.config import settings
from app.services.email import EmailService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kafka.response.consumer")


def start_consumer():
    logger.info("Starting permanent Kafka RPC Response Consumer Process...")
    kafka_url = getattr(settings, "KAFKA_URL", "kafka:29092")
    
    consumer = KafkaConsumer(
        "summary_responses",
        bootstrap_servers=kafka_url,
        group_id="celery-rpc-receiver-group",
        auto_offset_reset="latest",
        enable_auto_commit=True
    )
    
    for msg in consumer:
        try:
            response_data = json.loads(msg.value.decode("utf-8"))
            user_email = response_data.get("user_email")
            target_date_str = response_data.get("target_date")
            user_id = int(response_data.get("user_id", 0))
            llm_report_text = response_data.get("report_text")
            
            if user_email and target_date_str and llm_report_text:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        logger.info("Delivering email to %s (Attempt %s/%s)", user_email, attempt + 1, max_retries)
                        EmailService.send_daily_report_email(
                            user_id=user_id,
                            user_email=user_email,
                            yesterday=target_date,
                            custom_body=llm_report_text
                        )
                        break
                    except Exception as smtp_error:
                        if attempt == max_retries - 1:
                            raise smtp_error
                        logger.warning("SMTP failed, retrying in 5 seconds... Error: %s", smtp_error)
                        time.sleep(5)
                        
        except Exception as e:
            logger.error("CRITICAL: Failed to process message from Kafka: %s", e, exc_info=True)

if __name__ == "__main__":
    start_consumer()
