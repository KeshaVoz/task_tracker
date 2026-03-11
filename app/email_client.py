import smtplib
from app.config import settings


def get_smtp_server():
    server = smtplib.SMTP(settings.MAILJET_HOST, settings.MAILJET_PORT)
    return server