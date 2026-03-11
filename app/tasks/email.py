from app.celery_client import celery_client
from app.email_client import get_smtp_server
from app.services.tasks import TaskService
from app.dao.users import UserDAO
from app.config import settings
from app.schemas.email import SEmailData

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone


def _send_email(email_data: SEmailData):
    msg = MIMEMultipart()
    msg['From'] = settings.MAILJET_FROM
    msg['To'] = email_data.email
    msg['Subject'] = email_data.subject
    msg.attach(MIMEText(email_data.body, 'plain', 'utf-8'))
    
    server = get_smtp_server()
    server.send_message(msg)
    server.quit()


@celery_client.task(max_retries=3)
def send_welcome_email(user_email: str):
    print(f'send_welcome_email {user_email}')
    email_data = TaskService.prepare_welcome_email(user_email)
    _send_email(email_data)


@celery_client.task  
def send_daily_report():    
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    users = UserDAO.find_all_sync()
    
    for user in users:
        report = TaskService.prepare_daily_report(user.id, yesterday)
        emails = TaskService.prepare_emails_from_report(user.email, report)
        for email_data in emails:
            _send_email(email_data)
