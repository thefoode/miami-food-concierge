# Miami Food Concierge (SMS bot)

Followers text a phone number, an AI answers using your actual favorite restaurants (pulled live from a Google Sheet you maintain).

How it works: Twilio receives the text -> forwards it to this app's `/sms` webhook -> the app reads your Google Sheet + the conversation so far -> asks Claude to reply in your voice, grounded only in your list -> texts the reply back.

## 1. Set up your restaurant list (Google Sheet)

1. Create a new Google Sheet. Use these columns in row 1: `Category, Name, Neighborhood, Price, Notes` (see `sample-recommendations.csv` in this folder for the format - you can import it directly: File > Import > Upload).
2. Fill in your real favorites, one row per spot.
3. Publish it as CSV: **File > Share > Publish to web** > choose the specific sheet/tab > format **Comma-separated values (.csv)** > Publish.
4. Copy the URL it gives you - that's your `SHEET_CSV_URL`. It looks like:
   `https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?output=csv`

Whenever you edit the sheet, the bot picks up changes within 5 minutes automatically - no redeploy needed.

## 2. Get an Anthropic API key

Sign up / log in at https://console.anthropic.com, create an API key, and save it - that's your `ANTHROPIC_API_KEY`.

## 3. Set up Twilio (the phone number)

1. Sign up at https://www.twilio.com/try-twilio.
2. Buy a phone number with SMS capability (Phone Numbers > Buy a Number).
3. You won't set the webhook until after the app is deployed (step 5) - come back to this.

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

In another terminal, simulate an incoming text:

```bash
curl -X POST http://localhost:5000/sms -d "Body=best pizza in wynwood" -d "From=+15551234567"
```

You should get back TwiML XML containing the AI's reply.

## 5. Deploy to Railway

1. Sign up at https://railway.app (can use GitHub login).
2. New Project > Deploy from GitHub repo (push this folder to a GitHub repo first), or use the Railway CLI to deploy the folder directly.
3. In Railway's project settings, add environment variables: `ANTHROPIC_API_KEY`, `SHEET_CSV_URL`, `CREATOR_NAME`.
4. Railway auto-detects the `Procfile` and runs `gunicorn app:app`.
5. Once deployed, Railway gives you a public URL like `https://your-app.up.railway.app`.

## 6. Connect Twilio to your deployed app

1. In Twilio Console > Phone Numbers > your number > **Messaging** section.
2. Under "A message comes in", set the webhook to:
   `https://your-app.up.railway.app/sms`
   Method: `HTTP POST`.
3. Save.

Text your Twilio number and you should get a reply within a few seconds.

## Notes / next steps

- Conversation memory is in-process and resets if the app restarts, or after an hour of silence per phone number - fine for an MVP, easy to swap for a database later if you want persistence across restarts.
- `CREATOR_NAME` is used in the AI's system prompt so it can refer to whose recommendations these are.
- If you want to restrict who can text the bot (e.g. only approved followers), Twilio's console lets you see all inbound numbers - ask and I can add an allowlist/blocklist later.
- Costs to expect: Twilio number ~$1/mo + ~$0.0079 per text (US), Anthropic API usage is a few cents per conversation, Railway free tier covers light usage.
