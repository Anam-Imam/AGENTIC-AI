import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def email_configured():
    return all(os.getenv(k) for k in ("REMINDER_EMAIL", "REMINDER_PASSWORD", "REMINDER_TO"))


def send_email(subject, message):
    if not email_configured():
        return False, "Email settings are missing in .env."

    sender = os.getenv("REMINDER_EMAIL")
    password = os.getenv("REMINDER_PASSWORD")
    receiver = os.getenv("REMINDER_TO")
    host = os.getenv("REMINDER_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("REMINDER_SMTP_PORT", "465"))

    try:
        email = EmailMessage()
        email["From"] = sender
        email["To"] = receiver
        email["Subject"] = subject
        email.set_content(message)
        with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
            smtp.login(sender, password)
            smtp.send_message(email)
        return True, "Email sent successfully."
    except Exception as exc:
        return False, f"Email failed: {exc}"
