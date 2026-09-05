import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_interview_email(
    candidate_email: str,
    candidate_name: str,
    interview_url: str
):
    if not SMTP_EMAIL:
        raise ValueError("SMTP_EMAIL is not configured.")

    if not SMTP_PASSWORD:
        raise ValueError("SMTP_PASSWORD is not configured.")

    subject = "Technical Interview Invitation"

    body = f"""
Hello {candidate_name},

Thank you for applying.

We would like to invite you to complete
a technical interview.

Please use the following link to start:

{interview_url}

Please make sure you have a stable internet
connection before starting the interview.

Good luck!

AI Recruitment Team
"""

    message = MIMEMultipart()
    message["From"] = SMTP_EMAIL
    message["To"] = candidate_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(message)