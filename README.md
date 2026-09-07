# thefoode hotline (WhatsApp bot)

Followers message a WhatsApp number, an AI answers using your actual favorite restaurants (pulled live from a Google Sheet you maintain). Public-facing name: **thefoode hotline**.

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

### Going to production (done)

This app now runs in full production mode rather than on the shared test number:
1. **Business verification** completed for the Meta Business Portfolio (Business Verification: Verified).
2. A **permanent access token** was generated via a System User in Meta Business Settings (Business Settings > Users > System Users > generate token, expiration "Never", scoped to `whatsapp_business_management` + `whatsapp_business_messaging`). This doesn't expire like the 24-hour temporary token does.
3. A **dedicated phone number** was registered (not the shared test number) - a Google Voice number set up specifically for this bot. Registering it required: creating a WhatsApp Business Profile (display name, category, description), verifying the number via SMS code, and setting a 6-digit PIN (kept privately, needed only if the number is ever re-registered).
4. The System User was assigned access to this new WhatsApp Business Account (Business Settings > WhatsApp accounts > select account > Assign people > System User > enable "Messages" permission), and the app was subscribed to the account's webhook events via the Graph API (`POST /{WABA_ID}/subscribed_apps`).

One thing that looks like a bug but isn't: a **brand new number has no open conversation window** with anyone until they text it first. WhatsApp only allows free-form replies within 24 hours of the customer's last message (error 131047 "Re-engagement message" otherwise) - this is why the bot won't respond to a first-time number until that person has actually sent it a message for real.

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

Message the number from WhatsApp and you should get a reply within a few seconds.

## Current production status

- **Number:** +1 (305) 570-1131, display name "thefoode hotline" - fully registered, no tester/recipient limit (that restriction only applied to Meta's free shared test number, which this app no longer uses).
- **App:** published (not in Development mode).
- **Business:** verified (THEFOODE LLC).
- **Token:** permanent System User token, does not expire.
- Anyone can message the number and get a reply - no need to add them as a tester first.

## Notes / next steps

- Conversation memory is in-process and resets if the app restarts, or after an hour of silence per follower - fine for an MVP, easy to swap for a database later if you want persistence across restarts.
- `CREATOR_NAME` is used in the AI's system prompt so it can refer to whose recommendations these are.
- Costs to expect: Meta doesn't charge for the API itself or a monthly number fee. You only pay per message once you exceed Meta's free service-conversation tier (1,000/month) - and since this bot only ever replies to inbound messages, most of your traffic likely stays free. Anthropic API usage is a few cents per conversation. Railway free tier covers light usage.
- Still running on `sample-recommendations.csv`-style placeholder data until a real Google Sheet is published and `SHEET_CSV_URL` is updated in Railway.
