"""
This file contains the main code for the Flask application. 
It includes the routes for the main index page and the OpenAI API integration to analyze and generate essays.
"""

### Importing Required Libraries
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import stripe
import firebase_admin
from firebase_admin import credentials, firestore

from flask import (
    Flask,
    render_template,
    request,
    Response,
    send_from_directory,
    session,
    redirect,
    url_for,
    jsonify,
)

### Importing Required Files
from essayassist import analyze_essay, generate_essay

### End of Imports ###

load_dotenv('.env')

application = Flask(__name__)
application.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Initialize Firebase Admin SDK
db = None
try:
    if not firebase_admin._apps:
        # Try to use service account key file first
        service_account_path = 'firebase-service-account.json'
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized with service account key")
        else:
            # Try environment variable for service account JSON
            service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                import json
                service_account_data = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_data)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized with environment variable")
            else:
                # Fallback to default credentials
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {
                    'projectId': 'ivylab-d0d5e',
                })
                print("✅ Firebase initialized with default credentials")
    
    # Get Firestore client
    db = firestore.client()
    print("✅ Firestore initialized successfully")
except Exception as e:
    print(f"⚠️  Firestore initialization failed: {e}")
    print("📝 To enable Firestore, create a service account key file:")
    print("   1. Go to Firebase Console → Project Settings → Service Accounts")
    print("   2. Generate new private key")
    print("   3. Save as 'firebase-service-account.json' in project root")
    print("   4. Or set up Google Cloud credentials: gcloud auth application-default login")
    db = None

# Helper functions for Firestore operations
def get_user_subscription(user_id):
    """Get user subscription status from Firestore"""
    if db is None:
        print("⚠️  Firestore not available")
        return None, None, None
        
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get('subscription_status'), data.get('plan'), data.get('subscription_start_date')
        return None, None, None
    except Exception as e:
        print(f"Error getting user subscription: {e}")
        return None, None, None

def update_user_subscription(user_id, subscription_status, plan=None, start_date=None, stripe_subscription_id=None, stripe_customer_id=None):
    """Update user subscription status in Firestore"""
    if db is None:
        print("⚠️  Firestore not available - subscription not persisted")
        return False
        
    try:
        doc_ref = db.collection('users').document(user_id)
        update_data = {
            'subscription_status': subscription_status,
            'updated_at': datetime.now().isoformat()
        }
        if plan:
            update_data['plan'] = plan
        if start_date:
            update_data['subscription_start_date'] = start_date
        if stripe_subscription_id:
            update_data['stripe_subscription_id'] = stripe_subscription_id
        if stripe_customer_id:
            update_data['stripe_customer_id'] = stripe_customer_id
            
        doc_ref.set(update_data, merge=True)
        print(f"✅ Subscription saved to Firestore for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Error updating user subscription: {e}")
        return False

def validate_active_subscription(user_id):
    """Validate if user has an active subscription"""
    if not user_id:
        return False, "No user ID provided"
    
    # Check session first
    session_status = session.get('subscription_status')
    session_plan = session.get('plan')
    session_subscription_id = session.get('stripe_subscription_id')
    
    # Check Firestore for more reliable data
    firestore_status, firestore_plan, firestore_start_date = get_user_subscription(user_id)
    
    # Use Firestore data if available, otherwise fall back to session
    subscription_status = firestore_status or session_status
    plan = firestore_plan or session_plan
    stripe_subscription_id = session_subscription_id
    
    if not subscription_status or subscription_status != 'active':
        return False, "No active subscription found"
    
    if not plan:
        return False, "No subscription plan found"
    
    # If we have a Stripe subscription ID, check with Stripe
    if stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            if subscription.status == 'active':
                return True, "Active Stripe subscription found"
            elif subscription.status == 'past_due':
                return False, "Subscription payment failed - please update payment method"
            elif subscription.status == 'canceled':
                return False, "Subscription has been canceled"
            elif subscription.status == 'unpaid':
                return False, "Subscription is unpaid"
            else:
                return False, f"Subscription status: {subscription.status}"
                
        except stripe.error.StripeError as e:
            print(f"Error checking Stripe subscription: {e}")
            # Fall back to session-based validation
            pass
    
    # Fallback: If no Stripe subscription ID, use session-based validation
    # This handles legacy users or if Stripe check fails
    return True, "Active subscription found (session-based)"

def get_or_create_stripe_products():
    """Get or create Stripe products and prices for subscriptions"""
    try:
        # Check if products already exist
        products = stripe.Product.list(limit=10)
        weekly_product = None
        monthly_product = None
        
        for product in products.data:
            if product.name == "IvyLab Weekly Subscription":
                weekly_product = product
            elif product.name == "IvyLab Monthly Subscription":
                monthly_product = product
        
        # Create products if they don't exist
        if not weekly_product:
            weekly_product = stripe.Product.create(
                name="IvyLab Weekly Subscription",
                description="Weekly access to IvyLab essay analysis",
                type="service"
            )
            print(f"✅ Created weekly product: {weekly_product.id}")
        
        if not monthly_product:
            monthly_product = stripe.Product.create(
                name="IvyLab Monthly Subscription", 
                description="Monthly access to IvyLab essay analysis",
                type="service"
            )
            print(f"✅ Created monthly product: {monthly_product.id}")
        
        # Get or create prices
        weekly_price = None
        monthly_price = None
        
        # Check for existing prices
        prices = stripe.Price.list(limit=20)
        for price in prices.data:
            if price.product == weekly_product.id and price.recurring and price.recurring.interval == 'week':
                weekly_price = price
            elif price.product == monthly_product.id and price.recurring and price.recurring.interval == 'month':
                monthly_price = price
        
        # Create prices if they don't exist
        if not weekly_price:
            weekly_price = stripe.Price.create(
                unit_amount=799,  # $7.99 in cents
                currency='usd',
                recurring={'interval': 'week'},
                product=weekly_product.id,
            )
            print(f"✅ Created weekly price: {weekly_price.id}")
        
        if not monthly_price:
            monthly_price = stripe.Price.create(
                unit_amount=2999,  # $29.99 in cents
                currency='usd',
                recurring={'interval': 'month'},
                product=monthly_product.id,
            )
            print(f"✅ Created monthly price: {monthly_price.id}")
        
        return {
            'weekly': weekly_price.id,
            'monthly': monthly_price.id
        }
        
    except Exception as e:
        print(f"❌ Error creating Stripe products: {e}")
        return None

@application.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(application.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )

# page not found error
@application.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# === Authentication routes ===
@application.route("/auth")
def auth():
    return render_template("auth.html")

@application.route("/login", methods=["POST"])
def login():
    """Handle login verification"""
    try:
        data = request.get_json()
        user_id = data.get('uid')
        user_email = data.get('email')
        user_name = data.get('displayName', 'User')
        
        # Set session data
        session['user_id'] = user_id
        session['user_email'] = user_email
        session['user_name'] = user_name
        
        # Check if user already has a subscription
        subscription_status, plan, start_date = get_user_subscription(user_id)
        
        if subscription_status:
            # User has a subscription, set it in session
            session['subscription_status'] = subscription_status
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            print(f"🔍 User {user_id} logged in with existing subscription: {subscription_status}")
        else:
            print(f"🔍 User {user_id} logged in without subscription")
        
        return jsonify({"success": True, "message": "Login successful"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@application.route("/logout")
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('auth') + '?from=logout')

@application.route("/payment")
def payment():
    """Payment page"""
    # Check if user is authenticated
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    # Check subscription status from Firestore
    user_id = session.get('user_id')
    subscription_status, plan, start_date = get_user_subscription(user_id)
    
    if subscription_status == 'active':
        # Update session and redirect to main app
        session['subscription_status'] = subscription_status
        session['plan'] = plan
        session['subscription_start_date'] = start_date
        return redirect(url_for('index'))
    
    # Pass Stripe publishable key to template
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template("payment.html", stripe_publishable_key=stripe_publishable_key)


@application.route("/create-payment", methods=["POST"])
def create_payment():
    """Create Stripe subscription"""
    try:
        # Debug: Check if Stripe is properly configured
        if not stripe.api_key:
            return jsonify({"success": False, "message": "Stripe not configured"}), 500
            
        data = request.get_json()
        plan = data.get('plan')
        payment_method_id = data.get('payment_method_id')
        
        if plan not in ['weekly', 'monthly']:
            return jsonify({"success": False, "message": "Invalid plan"}), 400
        
        # Get or create Stripe products and prices
        price_ids = get_or_create_stripe_products()
        if not price_ids:
            return jsonify({"success": False, "message": "Failed to create subscription products"}), 500
        
        price_id = price_ids[plan]
        user_id = session.get('user_id')
        
        # Create or get customer
        customer = stripe.Customer.create(
            email=session.get('user_email'),
            name=session.get('user_name'),
            metadata={'user_id': user_id}
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            payment_method=payment_method_id,
            expand=['latest_invoice.payment_intent'],
            metadata={'user_id': user_id, 'plan': plan}
        )
        
        if subscription.status in ['active', 'trialing']:
            # Save subscription to Firestore
            start_date = str(datetime.now())
            
            print(f"🔍 Subscription created for user {user_id}, plan: {plan}, subscription_id: {subscription.id}")
            
            # Update session
            session['subscription_status'] = 'active'
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            session['stripe_subscription_id'] = subscription.id
            session['stripe_customer_id'] = customer.id
            
            # Save to Firestore
            update_user_subscription(user_id, 'active', plan, start_date, subscription.id, customer.id)
            
            return jsonify({
                "success": True, 
                "message": "Subscription created successfully",
                "subscription_id": subscription.id
            })
        else:
            return jsonify({"success": False, "message": f"Subscription failed: {subscription.status}"}), 400
            
    except stripe.error.CardError as e:
        return jsonify({"success": False, "message": f"Card error: {e.user_message}"}), 400
    except stripe.error.RateLimitError as e:
        return jsonify({"success": False, "message": "Rate limit exceeded"}), 429
    except stripe.error.InvalidRequestError as e:
        return jsonify({"success": False, "message": f"Invalid request: {str(e)}"}), 400
    except stripe.error.AuthenticationError as e:
        return jsonify({"success": False, "message": "Authentication failed"}), 401
    except stripe.error.APIConnectionError as e:
        return jsonify({"success": False, "message": "Network error"}), 500
    except stripe.error.StripeError as e:
        return jsonify({"success": False, "message": f"Stripe error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500

@application.route("/webhook", methods=["POST"])
def webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        )
    except ValueError:
        print("❌ Invalid payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid signature")
        return jsonify({"error": "Invalid signature"}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        print(f"✅ Subscription created: {subscription['id']}")
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        print(f"🔄 Subscription updated: {subscription['id']} - Status: {subscription['status']}")
        
        # Update user subscription status based on Stripe status
        user_id = subscription['metadata'].get('user_id')
        if user_id:
            if subscription['status'] == 'active':
                update_user_subscription(user_id, 'active', subscription['metadata'].get('plan'))
            elif subscription['status'] in ['canceled', 'unpaid', 'past_due']:
                update_user_subscription(user_id, 'inactive', subscription['metadata'].get('plan'))
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        print(f"❌ Subscription canceled: {subscription['id']}")
        
        # Mark subscription as inactive
        user_id = subscription['metadata'].get('user_id')
        if user_id:
            update_user_subscription(user_id, 'inactive', subscription['metadata'].get('plan'))
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        print(f"💰 Payment succeeded for subscription: {invoice['subscription']}")
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print(f"💳 Payment failed for subscription: {invoice['subscription']}")
        
        # Mark subscription as past_due
        user_id = invoice['metadata'].get('user_id')
        if user_id:
            update_user_subscription(user_id, 'past_due', invoice['metadata'].get('plan'))
    
    else:
        print(f"🤷 Unhandled event type: {event['type']}")
    
    return jsonify({"status": "success"})

@application.route("/subscription")
def subscription_management():
    """Subscription management page"""
    # Check if user is authenticated
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    user_id = session.get('user_id')
    stripe_subscription_id = session.get('stripe_subscription_id')
    
    subscription_info = None
    if stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            subscription_info = {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'plan': subscription.items.data[0].price.recurring.interval if subscription.items.data else 'unknown'
            }
        except stripe.error.StripeError as e:
            print(f"Error retrieving subscription: {e}")
    
    return render_template("subscription.html", subscription=subscription_info)

@application.route("/cancel-subscription", methods=["POST"])
def cancel_subscription():
    """Cancel user subscription"""
    try:
        user_id = session.get('user_id')
        stripe_subscription_id = session.get('stripe_subscription_id')
        
        if not stripe_subscription_id:
            return jsonify({"success": False, "message": "No active subscription found"}), 400
        
        # Cancel subscription at period end (don't cancel immediately)
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        print(f"🔍 Subscription {stripe_subscription_id} will be canceled at period end")
        
        # Update session
        session['subscription_canceled'] = True
        
        # Update Firestore
        update_user_subscription(user_id, 'canceled_at_period_end')
        
        return jsonify({
            "success": True, 
            "message": "Subscription will be canceled at the end of your current billing period",
            "cancel_at_period_end": subscription.cancel_at_period_end
        })
        
    except stripe.error.StripeError as e:
        return jsonify({"success": False, "message": f"Stripe error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@application.route("/reactivate-subscription", methods=["POST"])
def reactivate_subscription():
    """Reactivate a canceled subscription"""
    try:
        user_id = session.get('user_id')
        stripe_subscription_id = session.get('stripe_subscription_id')
        
        if not stripe_subscription_id:
            return jsonify({"success": False, "message": "No subscription found"}), 400
        
        # Reactivate subscription
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=False
        )
        
        print(f"🔍 Subscription {stripe_subscription_id} reactivated")
        
        # Update session
        session['subscription_canceled'] = False
        
        # Update Firestore
        update_user_subscription(user_id, 'active')
        
        return jsonify({
            "success": True, 
            "message": "Subscription reactivated successfully",
            "cancel_at_period_end": subscription.cancel_at_period_end
        })
        
    except stripe.error.StripeError as e:
        return jsonify({"success": False, "message": f"Stripe error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# === Main routes ===
@application.route("/landing")
def landing():
    """Landing page for new users"""
    return render_template("landing.html")

@application.route("/onboarding")
def onboarding():
    """Onboarding page - handles both new users and returning users"""
    # Check if user is already authenticated
    if 'user_id' in session:
        # User is already logged in, redirect to main app
        return redirect(url_for('index'))
    
    # User needs to sign up or log in, redirect to unified signup page
    return redirect(url_for('signup'))

@application.route("/index")
@application.route("/home")
@application.route("/")
def index():
    # Check if user is authenticated
    if 'user_id' not in session:
        print("🔍 No user_id in session, redirecting to landing")
        return redirect(url_for('landing'))
    
    # Check subscription status from Firestore
    user_id = session.get('user_id')
    subscription_status, plan, start_date = get_user_subscription(user_id)
    
    print(f"🔍 User {user_id} - Session subscription: {session.get('subscription_status')}")
    print(f"🔍 User {user_id} - Firestore subscription: {subscription_status}")
    
    # Use session data if Firestore is not available
    if not subscription_status:
        subscription_status = session.get('subscription_status')
        plan = session.get('plan')
        start_date = session.get('subscription_start_date')
    
    if not subscription_status:
        print(f"🔍 No subscription found, redirecting to payment")
        return redirect(url_for('payment'))
    
    print(f"🔍 Subscription found: {subscription_status}, redirecting to main app")
    return render_template("index.html")

@application.route("/check-auth")
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({"authenticated": True, "user": {
            "id": session.get('user_id'),
            "email": session.get('user_email'),
            "name": session.get('user_name')
        }})
    else:
        return jsonify({"authenticated": False})

# === Core functionality ===
@application.route("/analyze", methods=["POST"])
def analyze():
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    # Validate active subscription
    user_id = session.get('user_id')
    is_valid, message = validate_active_subscription(user_id)
    
    if not is_valid:
        print(f"❌ Subscription validation failed for user {user_id}: {message}")
        return jsonify({"error": f"Subscription required: {message}"}), 403
    
    essay_text = request.form["essay"]
    print(f"=== ANALYZE REQUEST START ===")
    print(f"User {user_id} - Subscription validated: {message}")
    print(f"Essay text length: {len(essay_text)}")
    print(f"Essay preview: {essay_text[:100]}...")
    
    result = analyze_essay(essay_text)
    print(f"Got result generator: {result}")
    
    def generate():
        chunk_count = 0
        try:
            for chunk in result:
                chunk_count += 1
                print(f"Yielding chunk {chunk_count}: '{chunk[:50]}...' (length: {len(chunk)})")
                yield chunk
            print(f"=== STREAMING COMPLETE - {chunk_count} chunks ===")
        except Exception as e:
            print(f"ERROR in generate(): {e}")
            yield f"Error: {str(e)}"
    
    print(f"=== STARTING STREAMING RESPONSE ===")
    return Response(generate(), mimetype="text/plain", headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
    })

@application.route("/demo-analyze", methods=["POST"])
def demo_analyze():
    """Demo analysis endpoint that returns blurred results"""
    data = request.get_json()
    essay_text = data.get('essay', '')
    
    if not essay_text or len(essay_text) < 100:
        return jsonify({"error": "Please provide an essay with at least 100 characters"}), 400
    
    print(f"=== DEMO ANALYZE REQUEST ===")
    print(f"Essay length: {len(essay_text)}")
    print(f"Essay preview: {essay_text[:100]}...")
    
    try:
        # Get the full analysis
        result = analyze_essay(essay_text)
        full_analysis = ""
        for chunk in result:
            full_analysis += chunk
        
        # Parse the analysis to extract key components
        lines = full_analysis.split('\n')
        score = "8.5"  # Default score
        strengths = "Strong personal voice and compelling narrative structure."
        improvements = "Consider adding more specific examples and refining your conclusion."
        
        # Try to extract actual data from the analysis
        for line in lines:
            if "Overall Score:" in line or "Score:" in line:
                # Extract score
                import re
                score_match = re.search(r'(\d+\.?\d*)/10', line)
                if score_match:
                    score = score_match.group(1)
            elif "Strengths:" in line or "Key Strengths:" in line:
                # Extract first strength
                strength_text = line.split(":", 1)[1].strip() if ":" in line else line
                if len(strength_text) > 10:
                    strengths = strength_text[:100] + "..." if len(strength_text) > 100 else strength_text
            elif "Improvements:" in line or "Areas for Improvement:" in line:
                # Extract first improvement
                improvement_text = line.split(":", 1)[1].strip() if ":" in line else line
                if len(improvement_text) > 10:
                    improvements = improvement_text[:100] + "..." if len(improvement_text) > 100 else improvement_text
        
        # Return demo results with blurred content
        return jsonify({
            "success": True,
            "score": score,
            "strengths": strengths,
            "improvements": improvements,
            "demo": True,
            "message": "This is a preview. Get the full detailed analysis with subscription."
        })
        
    except Exception as e:
        print(f"Demo analysis error: {e}")
        # Return fallback demo results
        return jsonify({
            "success": True,
            "score": "8.5",
            "strengths": "Strong personal voice and compelling narrative structure.",
            "improvements": "Consider adding more specific examples and refining your conclusion.",
            "demo": True,
            "message": "This is a preview. Get the full detailed analysis with subscription."
        })

@application.route("/generate", methods=["POST"])
def generate():
    # Check if user is authenticated
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    # Validate active subscription
    user_id = session.get('user_id')
    is_valid, message = validate_active_subscription(user_id)
    
    if not is_valid:
        print(f"❌ Subscription validation failed for user {user_id}: {message}")
        return jsonify({"error": f"Subscription required: {message}"}), 403
    
    outline_text = request.form["outline"]
    print(f"=== GENERATE REQUEST START ===")
    print(f"User {user_id} - Subscription validated: {message}")
    print(f"Outline text length: {len(outline_text)}")
    print(f"Outline preview: {outline_text[:100]}...")
    
    result = generate_essay(outline_text)
    print(f"Got result generator: {result}")
    
    def generate_stream():
        chunk_count = 0
        try:
            for chunk in result:
                chunk_count += 1
                print(f"Yielding chunk {chunk_count}: '{chunk[:50]}...' (length: {len(chunk)})")
                yield chunk
            print(f"=== GENERATE STREAMING COMPLETE - {chunk_count} chunks ===")
        except Exception as e:
            print(f"ERROR in generate_stream(): {e}")
            yield f"Error: {str(e)}"
    
    print(f"=== STARTING GENERATE STREAMING RESPONSE ===")
    return Response(generate_stream(), mimetype="text/event-stream", headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    })

if __name__ == "__main__":
    # Production configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    application.run(debug=debug_mode)
