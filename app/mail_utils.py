import os
import smtplib
from email.message import EmailMessage
from typing import Tuple


def _bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def send_contact_message(name: str, email: str, message: str) -> Tuple[bool, str]:
    """
    Send a contact form email using SMTP settings from environment variables.

    Required env vars (typical):
      - MAIL_SERVER (e.g., smtp.gmail.com)
      - MAIL_PORT (e.g., 587)
      - MAIL_USERNAME
      - MAIL_PASSWORD
      - MAIL_USE_TLS (1) or MAIL_USE_SSL (0/1)
      - MAIL_DEFAULT_SENDER (fallback: MAIL_USERNAME)
      - MAIL_RECIPIENT (where to deliver; fallback: MAIL_USERNAME)

    Returns (ok, error_message). error_message is empty on success.
    """
    server = os.getenv("MAIL_SERVER")
    port = int(os.getenv("MAIL_PORT", "0") or 0)
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls = _bool(os.getenv("MAIL_USE_TLS"), True)
    use_ssl = _bool(os.getenv("MAIL_USE_SSL"), False)
    default_sender = os.getenv("MAIL_DEFAULT_SENDER") or username
    recipient = os.getenv("MAIL_RECIPIENT") or username

    if not server or not port or not recipient or not default_sender:
        # Missing config; do a graceful no-op and report a friendly error
        return False, (
            "Email is not configured on the server yet. Please try again later or contact me via socials."
        )

    subject = "New contact message from website"

    body = (
        f"You received a new message from the website contact form.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n"
    )

    msg = EmailMessage()
    msg["From"] = default_sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(server, port) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(server, port) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        return True, ""
    except Exception as e:
        return False, f"Failed to send email: {e}"