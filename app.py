import os
import time
import logging

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from restaurant_data import get_restaurant_data
from ai import get_ai_reply

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


@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "unknown")

    logger.info("Incoming SMS from %s: %s", from_number, incoming_body)

    resp = MessagingResponse()

    if not incoming_body:
        resp.message('Text me a craving (like "best pizza in wynwood") and I\'ll hook you up with a spot!')
        return str(resp), 200, {"Content-Type": "text/xml"}

    try:
        restaurant_data = get_restaurant_data()
        history = get_history(from_number)
        reply_text, updated_history = get_ai_reply(incoming_body, history, restaurant_data)
        save_history(from_number, updated_history)
    except Exception:
        logger.exception("Failed to generate AI reply")
        reply_text = "Sorry, having a hiccup on my end, try again in a sec!"

    resp.message(reply_text)
    return str(resp), 200, {"Content-Type": "text/xml"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
