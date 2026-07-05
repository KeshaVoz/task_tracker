import smtplib
from app.config import settings

def get_smtp_server() -> smtplib.SMTP_SSL:
    return smtplib.SMTP_SSL(
        host=settings.SMTP_HOST, 
        port=settings.SMTP_PORT, 
        timeout=10.0
    )