# Miami Food Concierge (WhatsApp bot)

Followers message a WhatsApp number, an AI answers using your actual favorite restaurants (pulled live from a Google Sheet you maintain).

How it works: Twilio receives the WhatsApp message -> forwards it to this app's `/whatsapp` webhook -> the app reads your Google Sheet + the conversation so far -> asks Claude to reply in your voice, grounded only in your list -> sends the reply back over WhatsApp.

## 1. Set up your restaurant list (Google Sheet)

1. Create a new Google Sheet. Use these columns in row 1: `Category, Name, Neighborhood, Price, Notes` (see `sample-recommendations.csv` in this folder for the format - you can import it directly: File > Import > Upload).
2. Fill in your real favorites, one row per spot.
3. Publish it as CSV: **File > Share > Publish to web** > choose the specific sheet/tab > format **Comma-separated values (.csv)** > Publish.
4. Copy the URL it gives you - that's your `SHEET_CSV_URL`. It looks like:
   `https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?output=csv`

Whenever you edit the sheet, the bot picks up changes within 5 minutes automatically - no redeploy needed.

## 2. Get an Anthropic API key

Sign up / log in at https://console.anthropic.com, create an API key, and save it - that's your `ANTHROPIC_API_KEY`.

## 3. Set up Twilio for WhatsApp

Twilio gives you two ways to send/receive WhatsApp messages: a free **Sandbox** (instant, great for testing) and a **production WhatsApp Sender** (requires Meta approval, needed before you can share this with real followers).

### Start with the Sandbox (free, works immediately)

1. Sign up at https://www.twilio.com/try-twilio.
2. In the Twilio Console, go to **Messaging > Try it out > Send a WhatsApp message**. You'll get a shared Twilio sandbox number and a join code (like "join happy-tiger").
3. From your own phone, send that join code via WhatsApp to the sandbox number to link your account to it. Anyone you want to test with also needs to send that same join code once.
4. You won't set the webhook until after the app is deployed (step 5) - come back to this.

### Go to production when you're ready to launch to followers

1. In the Console, go to **Messaging > Senders > WhatsApp senders** and start the WhatsApp Sender request. This walks you through creating/connecting a Meta Business Account and WhatsApp Business Profile (name, logo, description).
2. Twilio submits this to Meta for approval - typically takes a few days.
3. Once approved, you get your own dedicated WhatsApp number (no join-code step for your followers - they just message it directly, or tap a `wa.me/1XXXXXXXXXX` link you share).
4. Repeat step 6 below with this production number's webhook instead of the sandbox's.

## 4. Run it locally to test (optional but recommended)

```bash
cd ~/miami-food-concierge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in ANTHROPIC_API_KEY, SHEET_CSV_URL, CREATOR_NAME
python app.py
```

In another terminal, simulate an incoming WhatsApp message:

```bash
curl -X POST http://localhost:5000/whatsapp -d "Body=best pizza in wynwood" -d "From=whatsapp:+15551234567"
```

You should get back TwiML XML containing the AI's reply.

## 5. Deploy to Railway

1. Sign up at https://railway.app (can use GitHub login).
2. New Project > Deploy from GitHub repo (push this folder to a GitHub repo first), or use the Railway CLI to deploy the folder directly.
3. In Railway's project settings, add environment variables: `ANTHROPIC_API_KEY`, `SHEET_CSV_URL`, `CREATOR_NAME`.
4. Railway auto-detects the `Procfile` and runs `gunicorn app:app`.
5. Once deployed, Railway gives you a public URL like `https://your-app.up.railway.app`.

## 6. Connect Twilio to your deployed app

**For the sandbox (testing):**
1. Console > Messaging > Try it out > Send a WhatsApp message > **Sandbox settings**.
2. Under "When a message comes in", set the webhook to:
   `https://your-app.up.railway.app/whatsapp`
   Method: `HTTP POST`.
3. Save.

**For production (once your WhatsApp Sender is approved):**
1. Console > Messaging > Senders > WhatsApp senders > your sender > **Configuration**.
2. Set the same webhook URL there.
3. Save.

Message the number on WhatsApp and you should get a reply within a few seconds.

## Notes / next steps

- Conversation memory is in-process and resets if the app restarts, or after an hour of silence per follower - fine for an MVP, easy to swap for a database later if you want persistence across restarts.
- `CREATOR_NAME` is used in the AI's system prompt so it can refer to whose recommendations these are.
- If you want to restrict who can message the bot (e.g. only approved followers), Twilio's console lets you see all inbound numbers - ask and I can add an allowlist/blocklist later.
- Costs to expect: WhatsApp Sender number is free from Twilio; Meta charges per-message only for business-initiated messages outside a 24-hour reply window - since this bot only ever replies to inbound messages, that's a free "service conversation" for the first 1,000/month and cheap after. Anthropic API usage is a few cents per conversation. Railway free tier covers light usage.
