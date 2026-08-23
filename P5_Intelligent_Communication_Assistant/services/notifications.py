import os
import smtplib
import ssl
from email.message import EmailMessage


class NotificationService:
    """Send email through the SMTP server configured in .env."""

    def send_email(self, to, subject, body):
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        sender = os.getenv("SMTP_FROM_EMAIL") or username

        if not all([host, username, password, sender]):
            return {
                "ok": False,
                "message": (
                    "SMTP is not configured. Add SMTP_HOST, SMTP_PORT, "
                    "SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM_EMAIL to .env."
                ),
            }

        if not to or "@" not in to or "." not in to.rsplit("@", 1)[-1]:
            return {"ok": False, "message": "Enter a valid recipient email address."}

        try:
            message = EmailMessage()
            message["From"] = sender
            message["To"] = to.strip()
            message["Subject"] = subject or "AURA Communication"
            message.set_content(body or "")

            context = ssl.create_default_context()

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(username, password)
                server.send_message(message)

            return {
                "ok": True,
                "message": f"Email sent successfully to {to.strip()}.",
            }

        except smtplib.SMTPAuthenticationError:
            return {
                "ok": False,
                "message": (
                    "SMTP authentication failed. Check SMTP_USERNAME/PASSWORD "
                    "and use an app password if your email provider requires one."
                ),
            }
        except smtplib.SMTPConnectError:
            return {
                "ok": False,
                "message": "Could not connect to the SMTP server. Check SMTP_HOST and SMTP_PORT.",
            }
        except smtplib.SMTPException as exc:
            return {"ok": False, "message": f"SMTP error: {exc}"}
        except Exception as exc:
            return {"ok": False, "message": f"Email error: {exc}"}

    def send_push(self, title, message):
        token = os.getenv("PUSHOVER_TOKEN")
        user = os.getenv("PUSHOVER_USER")
        if not token or not user:
            return {
                "ok": False,
                "message": "Pushover is not configured. Add PUSHOVER_TOKEN and PUSHOVER_USER to .env.",
            }

        try:
            import requests

            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={"token": token, "user": user, "title": title, "message": message},
                timeout=15,
            )
            if response.ok:
                return {"ok": True, "message": "Push notification sent successfully."}
            return {"ok": False, "message": f"Pushover returned HTTP {response.status_code}."}
        except Exception as exc:
            return {"ok": False, "message": f"Pushover error: {exc}"}
