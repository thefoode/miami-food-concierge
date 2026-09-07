# Miami Food Concierge (WhatsApp bot)

Followers message a WhatsApp number, an AI answers using your actual favorite restaurants (pulled live from a Google Sheet you maintain).

How it works: Meta's WhatsApp Cloud API receives the message -> forwards it to this app's `/webhook` -> the app reads your Google Sheet + the conversation so far -> asks Claude to reply in your voice, grounded only in your list -> the app calls Meta's API directly to send the reply back.

This talks to Meta directly (no Twilio or other middleman), so there's no monthly number fee and no markup on top of Meta's own rates - just Anthropic's usage cost, which is a few cents per conversation.

## 1. Set up your restaurant list (Google Sheet)

1. Create a new Google Sheet. Use these columns in row 1: `Category, Name, Neighborhood, Price, Notes` (see `sample-recommendations.csv` in this folder for the format - you can import it directly: File > Import > Upload).
2. Fill in your real favorites, one row per spot.
3. Publish it as CSV: **File > Share > Publish to web** > choose the specific sheet/tab > format **Comma-separated values (.csv)** > Publish.
4. Copy the URL it gives you - that's your `SHEET_CSV_URL`. It looks like:
   `https://docs.google.com/spreadsheets/d/e/2PACX-.../pub?output=csv`

Whenever you edit the sheet, the bot picks up changes within 5 minutes automatically - no redeploy needed.

## 2. Get an Anthropic API key

Sign up / log in at https://console.anthropic.com, create an API key, and save it - that's your `ANTHROPIC_API_KEY`.

## 3. Set up Meta's WhatsApp Cloud API (free to test, no payment info required)

1. Go to https://developers.facebook.com and sign up / log in with a Facebook account.
2. Click **My Apps > Create App**. Choose type **Business**, give it a name (e.g. "Miami Food Concierge").
3. In your new app's dashboard, find **WhatsApp** in the product list and click **Set up**.
4. This takes you to the WhatsApp > API Setup page. Here you'll see:
   - A **temporary access token** (valid ~24 hours - fine for testing, we'll set up a permanent one before going live)
   - A **test phone number** already provided by Meta, with its **Phone Number ID**
5. Copy the access token - that's `WHATSAPP_ACCESS_TOKEN`. Copy the Phone Number ID - that's `WHATSAPP_PHONE_NUMBER_ID`.
6. Under "To", add your own personal WhatsApp number as a test recipient (click **Manage phone number list**, add it, verify with the code Meta sends you). You can add up to 5 test numbers this way with zero cost and no business verification.
7. Pick any random string yourself (e.g. a long password) - that's `WHATSAPP_VERIFY_TOKEN`. You'll enter this same value in two places: Meta's webhook config (step 6 below) and Railway's env vars.

You won't finish the webhook config until the app is deployed (step 5) - come back to this.

### Going to production later (when you're ready to launch to followers)

The temporary token expires every 24 hours, and the test number can only message the 5 numbers you added. To go live:
1. Complete **Meta Business verification** for your app (Meta walks you through this in the App Dashboard).
2. Generate a **permanent access token** via a System User in Meta Business Settings (instead of the 24-hour temporary one).
3. Optionally request a dedicated WhatsApp number instead of the shared test number, and set your display name/profile.

I can walk you through this step by step whenever you're ready to launch publicly.

## 4. Run it locally to test (optional but recommended)

```bash
cd ~/miami-food-concierge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in all the values from steps 1-3
python app.py
```

## 5. Deploy to Railway

1. Sign up at https://railway.app (can use GitHub login).
2. New Project > Deploy from GitHub repo (push this folder to a GitHub repo first), or use the Railway CLI to deploy the folder directly.
3. In Railway's project settings, add environment variables: `ANTHROPIC_API_KEY`, `SHEET_CSV_URL`, `CREATOR_NAME`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.
4. Railway auto-detects the `Procfile` and runs `gunicorn app:app`.
5. Once deployed, Railway gives you a public URL like `https://your-app.up.railway.app`.

## 6. Connect Meta's webhook to your deployed app

1. Back in the Meta App Dashboard, go to **WhatsApp > Configuration**.
2. Under **Webhook**, click **Edit** and enter:
   - Callback URL: `https://your-app.up.railway.app/webhook`
   - Verify token: the same `WHATSAPP_VERIFY_TOKEN` value you put in Railway
3. Click **Verify and save** - Meta will hit your `/webhook` GET endpoint to confirm it matches, and the app should respond automatically.
4. Under **Webhook fields**, click **Manage** and subscribe to **messages**.

Message the test number from one of your verified test phones on WhatsApp and you should get a reply within a few seconds.

## Notes / next steps

- Conversation memory is in-process and resets if the app restarts, or after an hour of silence per follower - fine for an MVP, easy to swap for a database later if you want persistence across restarts.
- `CREATOR_NAME` is used in the AI's system prompt so it can refer to whose recommendations these are.
- Costs to expect: Meta doesn't charge for the API itself or a monthly number fee. You only pay per message once you exceed Meta's free service-conversation tier (1,000/month) - and since this bot only ever replies to inbound messages, most of your traffic likely stays free. Anthropic API usage is a few cents per conversation. Railway free tier covers light usage.
- The temporary access token from step 3 expires after ~24 hours during testing - if the bot suddenly stops replying, generate a new temporary token from the API Setup page and update it in Railway, or set up the permanent System User token described above.
