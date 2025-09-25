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

def update_user_subscription(user_id, subscription_status, plan=None, start_date=None):
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
            
        doc_ref.set(update_data, merge=True)
        print(f"✅ Subscription saved to Firestore for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Error updating user subscription: {e}")
        return False

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
    """Create Stripe payment intent"""
    try:
        # Debug: Check if Stripe is properly configured
        if not stripe.api_key:
            return jsonify({"success": False, "message": "Stripe not configured"}), 500
            
        data = request.get_json()
        plan = data.get('plan')
        payment_method_id = data.get('payment_method_id')
        
        # Define pricing
        prices = {
            'monthly': 1900,  # $19.00 in cents
            'annual': 14900   # $149.00 in cents
        }
        
        if plan not in prices:
            return jsonify({"success": False, "message": "Invalid plan"}), 400
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=prices[plan],
            currency='usd',
            payment_method=payment_method_id,
            confirm=True,
            return_url=request.url_root
        )
        
        if intent.status == 'succeeded':
            # Save subscription to Firestore
            user_id = session.get('user_id')
            start_date = str(datetime.now())
            
            print(f"🔍 Payment successful for user {user_id}, plan: {plan}")
            
            # Update session first
            session['subscription_status'] = 'active'
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            
            print(f"🔍 Session updated: {session.get('subscription_status')}")
            
            # Try to save to Firestore (optional)
            update_user_subscription(user_id, 'active', plan, start_date)
            
            return jsonify({"success": True, "message": "Payment successful"})
        else:
            return jsonify({"success": False, "message": "Payment failed"}), 400
            
    except stripe.error.CardError as e:
        return jsonify({"success": False, "message": f"Card error: {e.user_message}"}), 400
    except stripe.error.StripeError as e:
        return jsonify({"success": False, "message": f"Stripe error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 400

# === Main routes ===
@application.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

@application.route("/index")
@application.route("/home")
@application.route("/")
def index():
    # Check if user is authenticated
    if 'user_id' not in session:
        print("🔍 No user_id in session, redirecting to onboarding")
        return redirect(url_for('onboarding'))
    
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
    essay_text = request.form["essay"]
    print(f"=== ANALYZE REQUEST START ===")
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

@application.route("/generate", methods=["POST"])
def generate():
    outline_text = request.form["outline"]
    print(f"=== GENERATE REQUEST START ===")
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
    port = int(os.environ.get('PORT', 5004))
    application.run(debug=debug_mode, port=port, host='0.0.0.0')
