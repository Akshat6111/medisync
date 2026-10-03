import logging
import os
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


def send_email_reminder(to_email: str, subject: str, message: str) -> bool:
    """
    Sends an email reminder using Resend API if RESEND_API_KEY is configured.
    Falls back gracefully to logging delivery in local/test environments.
    """
    if not to_email:
        logger.warning("send_email_reminder called with empty recipient email")
        return False

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL", "MediSync <onboarding@resend.dev>")

    if api_key and not api_key.startswith("mock"):
        try:
            resp = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_email,
                    "to": [to_email],
                    "subject": subject,
                    "text": message,
                },
                timeout=8.0,
            )
            if resp.status_code in (200, 201):
                email_id = resp.json().get("id", "delivered")
                logger.info(f"Email reminder successfully delivered via Resend to {to_email} (ID: {email_id})")
                return True
            else:
                logger.warning(f"Resend API response {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to deliver email reminder via Resend: {e}")
            return False
    else:
        # Development / Test mode: delivery simulation
        logger.info(f"[EMAIL REMINDER DELIVERED] Recipient: {to_email} | Subject: '{subject}' | Message: '{message}'")
        return True
