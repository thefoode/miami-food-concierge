import os
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"


def send_message(to, body):
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not access_token or not phone_number_id:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID not set")

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    request_obj = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=10) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        logger.error("WhatsApp send failed: %s %s", e.code, e.read())
        raise


def extract_incoming_message(payload):
    """Returns (from_number, text_body) or (None, None) if there's nothing to handle
    (e.g. a delivery-status update rather than a new message)."""
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        messages = value.get("messages")
        if not messages:
            return None, None
        message = messages[0]
        from_number = message.get("from")
        if message.get("type") != "text":
            return from_number, None
        text_body = message.get("text", {}).get("body", "")
        return from_number, text_body
    except (KeyError, IndexError):
        return None, None
