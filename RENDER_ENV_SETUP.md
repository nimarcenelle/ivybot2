# Render Environment Variables Setup Guide

When deploying to Render, you need to set environment variables in the Render dashboard. The `.env` file is only for local development and should NOT be committed to git.

## Required Environment Variables

Set these in your Render service dashboard under **Environment**:

### 1. OpenAI API Key (REQUIRED)
```
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```
- Get your key from: https://platform.openai.com/api-keys
- This is required for the AI essay analysis, generation, and rewriting features
- Without this, the app will return demo responses

### 2. Flask Secret Key (REQUIRED)
```
SECRET_KEY=your-super-secret-random-string-here
```
- Generate a random secret key (e.g., use `openssl rand -hex 32`)
- Used for Flask session management

### 3. Stripe Keys (REQUIRED for payments)
```
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here
```
- Get from: https://dashboard.stripe.com/apikeys
- Use **live keys** for production, **test keys** for testing
- Test keys start with `sk_test_` and `pk_test_`
- Live keys start with `sk_live_` and `pk_live_`

### 4. Stripe Webhook Secret (OPTIONAL but recommended)
```
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```
- Get from: Stripe Dashboard → Developers → Webhooks
- Only needed if you want webhook functionality for subscription events

### 5. Firebase Service Account JSON (REQUIRED for user data)
```
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id",...}
```
- Get from: Firebase Console → Project Settings → Service Accounts → Generate New Private Key
- Copy the entire JSON object as a single-line string
- **Important**: Escape quotes properly or use Render's JSON editor if available
- Alternative: You can also place `firebase-service-account.json` file in your repo (less secure)

### 6. Flask Debug Mode (OPTIONAL)
```
FLASK_DEBUG=False
```
- Set to `True` for development, `False` for production
- Defaults to `False` if not set

### 7. Port (OPTIONAL)
```
PORT=5000
```
- Render automatically sets this, but you can override if needed
- Defaults to 5000 if not set

## How to Set Environment Variables on Render

1. **Go to your Render Dashboard**
   - Navigate to your service (web service)

2. **Click on "Environment"** in the left sidebar

3. **Add each variable:**
   - Click "Add Environment Variable"
   - Enter the key (e.g., `OPENAI_API_KEY`)
   - Enter the value (e.g., `sk-...`)
   - Click "Save Changes"

4. **Redeploy your service:**
   - After adding variables, Render will automatically redeploy
   - Or manually trigger a redeploy from the "Manual Deploy" section

## Verification

After setting up environment variables, check your Render logs to verify:

1. **OpenAI API Key**: Look for successful API calls (no demo responses)
2. **Stripe**: Look for messages like:
   - `🔴 STRIPE LIVE MODE ACTIVE` or `🟡 STRIPE TEST MODE ACTIVE`
3. **Firebase**: Look for:
   - `✅ Firebase initialized with environment variable`
   - `✅ Firestore initialized successfully`

## Troubleshooting

### Issue: Getting demo responses
- **Solution**: Check that `OPENAI_API_KEY` is set correctly in Render
- Verify the key is valid by testing it in OpenAI's API playground
- Check Render logs for error messages

### Issue: Firebase not initializing
- **Solution**: Verify `FIREBASE_SERVICE_ACCOUNT_JSON` is set correctly
- Make sure the JSON is on a single line with escaped quotes
- Check that the service account has proper permissions

### Issue: Stripe payments not working
- **Solution**: Verify both `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` are set
- Make sure you're using matching keys (both test or both live)
- Check Stripe dashboard for API key status

## Security Best Practices

1. **Never commit `.env` files to git**
   - Add `.env` to your `.gitignore`
   
2. **Use different keys for development and production**
   - Use test Stripe keys for development
   - Use live Stripe keys only in production

3. **Rotate keys if exposed**
   - If you accidentally commit keys, revoke them immediately
   - Generate new keys and update Render

4. **Use Render's environment variable encryption**
   - Render automatically encrypts environment variables
   - They're only visible to you and your team members with access

## Quick Checklist

Before deploying, make sure you have:
- [ ] `OPENAI_API_KEY` set
- [ ] `SECRET_KEY` set
- [ ] `STRIPE_SECRET_KEY` set
- [ ] `STRIPE_PUBLISHABLE_KEY` set
- [ ] `FIREBASE_SERVICE_ACCOUNT_JSON` set (or `firebase-service-account.json` file)
- [ ] All keys are valid and active
- [ ] Service has been redeployed after adding variables

