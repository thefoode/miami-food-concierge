import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
CREATOR_NAME = os.environ.get("CREATOR_NAME", "your Miami food guy")


def _format_restaurant_data(rows):
    if not rows:
        return "(No restaurant data loaded yet.)"
    lines = []
    for row in rows:
        parts = [f"{key}: {value}" for key, value in row.items() if value]
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _format_faq_data(rows):
    lines = []
    for row in rows:
        question = row.get("Question", "").strip()
        answer = row.get("Answer", "").strip()
        if question and answer:
            lines.append(f"Q: {question}\nA: {answer}")
    return "\n\n".join(lines)


def build_system_prompt(restaurant_data, faq_data=None):
    data_text = _format_restaurant_data(restaurant_data)
    faq_text = _format_faq_data(faq_data or [])
    faq_section = f"\n\nCommon questions and how to answer them:\n{faq_text}\n" if faq_text else ""

    return f"""You are a texting concierge bot for {CREATOR_NAME}, a Miami food content creator. Followers text you asking for restaurant recommendations. Answer ONLY using the recommendations list below - these are the creator's actual favorite spots. Never invent restaurants that aren't in the list.

Style rules:
- Keep replies SHORT, like a real text message (1-4 sentences max).
- Sound like a friend texting back, not a formal assistant. Casual, warm, a little hype.
- If asked for a category or area with multiple matches, give 1-3 top picks, not the whole list.
- If nothing in the list matches what they're asking for, say so honestly and suggest the closest thing you do have, or ask a clarifying question (e.g. neighborhood, budget).
- Don't use markdown formatting - this is a plain text message.
- Do not mention that you are an AI, a bot, or that you're reading from a list or spreadsheet.
- If a follower asks something covered in the common questions list below, use that as your answer (in your own words, still short and casual) rather than guessing.

Creator's Miami recommendations (each line is one spot):
{data_text}{faq_section}
"""


def get_ai_reply(user_message, history, restaurant_data, faq_data=None):
    system_prompt = build_system_prompt(restaurant_data, faq_data)
    messages = history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system_prompt,
        messages=messages,
    )

    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    updated_history = messages + [{"role": "assistant", "content": reply_text}]
    return reply_text, updated_history
