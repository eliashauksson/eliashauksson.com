import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Tuple

logger = logging.getLogger(__name__)
SMTP_TIMEOUT_SECONDS = 15
CONFIG_ERROR = (
    "Email is not configured on the server yet. Please try again later or contact me via socials."
)
SEND_ERROR = (
    "Email could not be sent right now. Please try again later or contact me via socials."
)


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
    port_raw = os.getenv("MAIL_PORT", "0") or 0
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls = _bool(os.getenv("MAIL_USE_TLS"), True)
    use_ssl = _bool(os.getenv("MAIL_USE_SSL"), False)
    default_sender = os.getenv("MAIL_DEFAULT_SENDER") or username
    recipient = os.getenv("MAIL_RECIPIENT") or username

    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        logger.error("Invalid MAIL_PORT value: %r", port_raw)
        return False, CONFIG_ERROR

    if not server or not port or not recipient or not default_sender:
        logger.error(
            "Missing email configuration: server=%s port=%s recipient=%s sender=%s",
            bool(server),
            bool(port),
            bool(recipient),
            bool(default_sender),
        )
        return False, CONFIG_ERROR

    safe_name = " ".join(name.split())
    subject = f"[eliashauksson.com] Contact from {safe_name}"

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
    msg["Reply-To"] = email
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(server, port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(server, port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        return True, ""
    except smtplib.SMTPException:
        logger.exception("SMTP error while sending contact form email")
        return False, SEND_ERROR
    except OSError:
        logger.exception("Network error while sending contact form email")
        return False, SEND_ERROR
    except Exception:
        logger.exception("Unexpected error while sending contact form email")
        return False, SEND_ERROR
