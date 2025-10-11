# Stripe Payment Setup Guide

## 1. Create Stripe Account

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Sign up for a free account
3. Complete account verification

## 2. Get Your API Keys

1. In Stripe Dashboard, go to **Developers** → **API keys**
2. Copy your **Publishable key** (starts with `pk_test_`)
3. Copy your **Secret key** (starts with `sk_test_`)

## 3. Update Configuration

### Update Payment Template
1. Open `templates/payment.html`
2. Find line with `const stripe = Stripe('pk_test_your_publishable_key_here');`
3. Replace with your actual publishable key:
```javascript
const stripe = Stripe('pk_test_your_actual_publishable_key');
```

### Update Environment Variables
1. Add to your `.env` file:
```
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
```

## 4. Test the Payment Flow

1. Start your app: `python3 application.py`
2. Go through the signup process
3. You should be redirected to the payment page
4. Try the "Free Trial" option first
5. Test with Stripe test card: `4242 4242 4242 4242`

## 5. Payment Plans

### Free Trial
- 3 essays free
- 7-day access
- No payment required

### Monthly Plan
- $19/month
- Unlimited essays
- Advanced features

### Annual Plan
- $149/year (35% savings)
- All features included

## 6. Test Cards (Stripe)

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

## 7. Production Setup

When ready for production:
1. Switch to live API keys in Stripe Dashboard
2. Update your `.env` file with live keys
3. Update the payment template with live publishable key
4. Test with real payment methods

## Features Included

- ✅ **Free trial** option
- ✅ **Monthly and annual** plans
- ✅ **Stripe payment** integration
- ✅ **Session management** for subscription status
- ✅ **Automatic redirects** based on payment status
- ✅ **Beautiful UI** matching your app design
- ✅ **Mobile responsive** design

## Security Notes

- Never expose your secret key in frontend code
- Use environment variables for sensitive data
- Stripe handles all payment processing securely
- User payment data is never stored on your server
