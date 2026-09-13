import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

LOG_WEBHOOK_URL = os.environ.get("LOG_WEBHOOK_URL")


def log_conversation(phone_number, message, reply):
    if not LOG_WEBHOOK_URL:
        return

    payload = json.dumps({
        "phone": phone_number,
        "message": message,
        "reply": reply,
    }).encode("utf-8")

    req = urllib.request.Request(
        LOG_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        logger.exception("Failed to log conversation to sheet")
