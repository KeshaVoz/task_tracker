import logging
from datetime import date
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings
from app.email_client import get_smtp_server
from app.schemas.email import SEmailData


logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def _send_email_batch(emails_data: List[SEmailData]) -> None:
        if not emails_data:
            return

        try:
            with get_smtp_server() as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                for email_data in emails_data:
                    msg = MIMEMultipart()
                    msg["From"] = settings.SMTP_FROM
                    msg["To"] = email_data.email
                    msg["Subject"] = email_data.subject
                    msg.attach(MIMEText(email_data.body, "plain", "utf-8"))
                    server.send_message(msg)
        except Exception as e:
            logger.error("SMTP batch send failed: %s", e, exc_info=True)
            raise e


    @classmethod
    def send_welcome_email(cls, user_email: str) -> None:
        email_data = SEmailData(
            email=user_email,
            subject="Welcome to Task Tracker!",
            body="Hello!\n\nYou have successfully registered in Task Tracker.\n"
                 "Now you can create and manage your tasks.",
        )
        cls._send_email_batch([email_data])

    @classmethod
    def send_daily_report_email(cls, user_id: int, user_email: str, yesterday: date, custom_body: str) -> None:
        logger.info("Preparing to send AI daily report email to %s", user_email)
        
        subject = f"📊 Your AI Daily Task Report for {yesterday}"
        
        email_data = SEmailData(
            email=user_email,
            subject=subject,
            body=custom_body
        )
        
        cls._send_email_batch([email_data])