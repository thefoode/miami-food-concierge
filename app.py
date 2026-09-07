import os
import time
import logging

from flask import Flask, request

from restaurant_data import get_restaurant_data
from ai import get_ai_reply
from meta_whatsapp import send_message, extract_incoming_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# phone_number -> {"messages": [...], "last_active": timestamp}
conversations = {}
CONVERSATION_TTL_SECONDS = 60 * 60  # forget context after an hour of silence
MAX_HISTORY_MESSAGES = 10


def get_history(phone_number):
    convo = conversations.get(phone_number)
    if convo and time.time() - convo["last_active"] < CONVERSATION_TTL_SECONDS:
        return convo["messages"]
    return []


def save_history(phone_number, messages):
    conversations[phone_number] = {
        "messages": messages[-MAX_HISTORY_MESSAGES:],
        "last_active": time.time(),
    }


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")

    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    payload = request.get_json(silent=True) or {}
    from_number, incoming_body = extract_incoming_message(payload)

    if not from_number:
        # Delivery/status updates, or payloads with nothing to reply to.
        return "", 200

    logger.info("Incoming WhatsApp message from %s: %s", from_number, incoming_body)

    if not incoming_body:
        reply_text = 'Text me a craving (like "best pizza in wynwood") and I\'ll hook you up with a spot!'
    else:
        try:
            restaurant_data = get_restaurant_data()
            history = get_history(from_number)
            reply_text, updated_history = get_ai_reply(incoming_body, history, restaurant_data)
            save_history(from_number, updated_history)
        except Exception:
            logger.exception("Failed to generate AI reply")
            reply_text = "Sorry, having a hiccup on my end, try again in a sec!"

    try:
        send_message(from_number, reply_text)
    except Exception:
        logger.exception("Failed to send WhatsApp reply")

    return "", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
