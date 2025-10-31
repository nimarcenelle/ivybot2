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
from firebase_admin import credentials, firestore, auth as firebase_auth

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
    make_response,
)

### Importing Required Files
from essayassist import analyze_essay, generate_essay

### End of Imports ###

load_dotenv('.env')

application = Flask(__name__)
application.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Function to set no-cache headers
def set_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Log Stripe mode for verification
if stripe.api_key:
    if stripe.api_key.startswith('sk_live_'):
        print("🔴 STRIPE LIVE MODE ACTIVE - Using live keys")
    elif stripe.api_key.startswith('sk_test_'):
        print("🟡 STRIPE TEST MODE ACTIVE - Using test keys")
    else:
        print("⚠️  STRIPE KEY FORMAT UNKNOWN")
    print(f"🔑 Stripe Secret Key: {stripe.api_key[:12]}...")
    print(f"🔑 Stripe Publishable Key: {stripe_publishable_key[:12] if stripe_publishable_key else 'None'}...")
else:
    print("❌ NO STRIPE SECRET KEY FOUND!")

# Initialize Firebase Admin SDK
db = None

# Legacy user email whitelist - add emails here that should use legacy login
LEGACY_USER_EMAILS = {
    # Add specific emails here that should use legacy authentication
    "test@example.com",  # Test email for demonstration
    "baloney2@gmail.com",  # Legacy user
    "bellanotar1@gmail.com",  # Legacy user
    # Example: "another@example.com",
}
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

def update_user_subscription(user_id, subscription_status, plan=None, start_date=None, stripe_subscription_id=None, stripe_customer_id=None, user_email=None, user_name=None):
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
        if user_email:
            update_data['user_email'] = user_email
        if user_name:
            update_data['user_name'] = user_name
            
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
        
        # Expected amounts in cents
        expected_weekly_amount = 999  # $9.99
        expected_monthly_amount = 2499  # $24.99
        
        # Check for existing prices with correct amounts
        prices = stripe.Price.list(limit=20)
        for price in prices.data:
            if price.product == weekly_product.id and price.recurring and price.recurring.interval == 'week':
                # Only use this price if it matches our expected amount
                if price.unit_amount == expected_weekly_amount:
                    weekly_price = price
                    print(f"✅ Found existing weekly price: {weekly_price.id} (${weekly_price.unit_amount/100:.2f})")
            elif price.product == monthly_product.id and price.recurring and price.recurring.interval == 'month':
                # Only use this price if it matches our expected amount
                if price.unit_amount == expected_monthly_amount:
                    monthly_price = price
                    print(f"✅ Found existing monthly price: {monthly_price.id} (${monthly_price.unit_amount/100:.2f})")
        
        # Create prices if they don't exist or have wrong amounts
        if not weekly_price:
            weekly_price = stripe.Price.create(
                unit_amount=expected_weekly_amount,  # $9.99 in cents
                currency='usd',
                recurring={'interval': 'week'},
                product=weekly_product.id,
            )
            print(f"✅ Created weekly price: {weekly_price.id} (${expected_weekly_amount/100:.2f})")
        
        if not monthly_price:
            monthly_price = stripe.Price.create(
                unit_amount=expected_monthly_amount,  # $24.99 in cents
                currency='usd',
                recurring={'interval': 'month'},
                product=monthly_product.id,
            )
            print(f"✅ Created monthly price: {monthly_price.id} (${expected_monthly_amount/100:.2f})")
        
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
    response = make_response(render_template("auth.html"))
    return set_no_cache_headers(response)

@application.route("/login", methods=["POST"])
def login():
    """Handle user login with Firebase Auth token verification or legacy login for whitelisted emails"""
    print("🚀 LOGIN ENDPOINT CALLED!")
    try:
        data = request.get_json()
        print(f"🚀 Login request data: {data}")
        id_token = data.get('idToken')
        uid = data.get('uid')
        email = data.get('email')
        display_name = data.get('displayName')
        print(f"🚀 Extracted: id_token={bool(id_token)}, uid={uid}, email={email}")
        
        # Check if this is a legacy user (email in whitelist but no Firebase Auth token)
        if email and email in LEGACY_USER_EMAILS and (not id_token or not uid):
            print(f"🔍 Legacy user detected: {email}")
            return legacy_login_for_email(email)
        
        # Regular Firebase Auth login
        if not id_token or not uid:
            return jsonify({"success": False, "message": "Wrong username or password"}), 400
        
        # Verify the Firebase Auth token
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            
            # Ensure the UID matches
            if firebase_uid != uid:
                return jsonify({"success": False, "message": "Token UID mismatch"}), 401
                
            print(f"🔍 Firebase Auth token verified for UID: {firebase_uid}")
            
        except firebase_auth.InvalidIdTokenError:
            return jsonify({"success": False, "message": "Invalid Firebase Auth token"}), 401
        except firebase_auth.ExpiredIdTokenError:
            return jsonify({"success": False, "message": "Firebase Auth token expired"}), 401
        except Exception as e:
            print(f"Error verifying Firebase Auth token: {e}")
            return jsonify({"success": False, "message": "Token verification failed"}), 401
        
        # Use Firebase UID as the user_id for consistency
        user_id = firebase_uid
        
        # Check if user exists in Firestore, create if not
        user_exists = False
        if db:
            try:
                doc_ref = db.collection('users').document(user_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    user_data = doc.to_dict()
                    user_exists = True
                    print(f"🔍 User found in Firestore: {user_id}")
                else:
                    # Create user document if it doesn't exist
                    user_data = {
                        'user_email': email,
                        'user_name': display_name or email.split('@')[0],
                        'firebase_uid': firebase_uid,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    doc_ref.set(user_data)
                    print(f"🔍 Created new user in Firestore: {user_id}")
                    
            except Exception as e:
                print(f"Error checking/creating user in Firestore: {e}")
                return jsonify({"success": False, "message": "Database error"}), 500
        else:
            print("⚠️  Firestore not available - using session-only mode")
        
        # Set session data
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = display_name or email.split('@')[0]
        session['firebase_uid'] = firebase_uid
        
        # Get user subscription status
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
        print(f"Login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

def legacy_login_for_email(email):
    """Handle legacy login for whitelisted email addresses"""
    try:
        print(f"🔍 Processing legacy login for email: {email}")
        
        # Search for user by email in Firestore
        user_id = None
        user_data = None
        if db:
            try:
                # Query users collection by email
                users_ref = db.collection('users')
                query = users_ref.where('user_email', '==', email).limit(1)
                docs = query.get()
                
                print(f"🔍 Found {len(docs)} documents for email: {email}")
                
                if docs:
                    doc = docs[0]
                    user_data = doc.to_dict()
                    user_id = doc.id
                    print(f"🔍 Legacy user found: {user_id}")
                    print(f"🔍 User data: {user_data}")
                else:
                    print(f"🔍 No legacy user found with email: {email}")
                    return jsonify({"success": False, "message": "No account found with this email. Please sign up for a new account."}), 401
                    
            except Exception as e:
                print(f"Error checking user in Firestore: {e}")
                return jsonify({"success": False, "message": "Database error"}), 500
        else:
            print("⚠️  Firestore not available - legacy login not possible")
            return jsonify({"success": False, "message": "Database not available"}), 500
        
        # Set session data for legacy user
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = user_data.get('user_name', email.split('@')[0])
        session['legacy_user'] = True  # Flag to indicate this is a legacy user
        
        # Get user subscription status
        subscription_status, plan, start_date = get_user_subscription(user_id)
        
        if subscription_status:
            # User has a subscription, set it in session
            session['subscription_status'] = subscription_status
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            print(f"🔍 Legacy user {user_id} logged in with existing subscription: {subscription_status}")
        else:
            print(f"🔍 Legacy user {user_id} logged in without subscription")
        
        return jsonify({
            "success": True, 
            "message": "Login successful",
            "legacy_user": True
        })
    except Exception as e:
        print(f"Legacy login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@application.route("/legacy-login", methods=["POST"])
def legacy_login():
    """Handle legacy user login for existing users (temporary migration support)"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        print(f"🔍 Legacy login attempt for email: {email}")
        
        # Search for user by email in Firestore
        user_id = None
        user_data = None
        if db:
            try:
                # Query users collection by email
                users_ref = db.collection('users')
                query = users_ref.where('user_email', '==', email).limit(1)
                docs = query.get()
                
                print(f"🔍 Found {len(docs)} documents for email: {email}")
                
                if docs:
                    doc = docs[0]
                    user_data = doc.to_dict()
                    user_id = doc.id
                    print(f"🔍 Legacy user found: {user_id}")
                    print(f"🔍 User data: {user_data}")
                else:
                    print(f"🔍 No legacy user found with email: {email}")
                    return jsonify({"success": False, "message": "No account found with this email. Please sign up for a new account."}), 401
                    
            except Exception as e:
                print(f"Error checking user in Firestore: {e}")
                return jsonify({"success": False, "message": "Database error"}), 500
        else:
            print("⚠️  Firestore not available - legacy login not possible")
            return jsonify({"success": False, "message": "Database not available"}), 500
        
        # Set session data for legacy user
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = user_data.get('user_name', email.split('@')[0])
        session['legacy_user'] = True  # Flag to indicate this is a legacy user
        
        # Get user subscription status
        subscription_status, plan, start_date = get_user_subscription(user_id)
        
        if subscription_status:
            # User has a subscription, set it in session
            session['subscription_status'] = subscription_status
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            print(f"🔍 Legacy user {user_id} logged in with existing subscription: {subscription_status}")
        else:
            print(f"🔍 Legacy user {user_id} logged in without subscription")
        
        return jsonify({
            "success": True, 
            "message": "Legacy login successful. Please consider upgrading to secure authentication.",
            "legacy_user": True,
            "migration_required": True
        })
    except Exception as e:
        print(f"Legacy login error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@application.route("/migrate-to-firebase", methods=["POST"])
def migrate_to_firebase():
    """Migrate a legacy user to Firebase Auth"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        uid = data.get('uid')
        email = data.get('email')
        display_name = data.get('displayName')
        legacy_user_id = data.get('legacyUserId')
        
        if not all([id_token, uid, email, legacy_user_id]):
            return jsonify({"success": False, "message": "Missing required fields for migration"}), 400
        
        # Verify the Firebase Auth token
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded_token['uid']
            
            # Ensure the UID matches
            if firebase_uid != uid:
                return jsonify({"success": False, "message": "Token UID mismatch"}), 401
                
            print(f"🔍 Firebase Auth token verified for migration: {firebase_uid}")
            
        except firebase_auth.InvalidIdTokenError:
            return jsonify({"success": False, "message": "Invalid Firebase Auth token"}), 401
        except firebase_auth.ExpiredIdTokenError:
            return jsonify({"success": False, "message": "Firebase Auth token expired"}), 401
        except Exception as e:
            print(f"Error verifying Firebase Auth token: {e}")
            return jsonify({"success": False, "message": "Token verification failed"}), 401
        
        # Get legacy user data
        if not db:
            return jsonify({"success": False, "message": "Database not available"}), 500
            
        try:
            legacy_doc_ref = db.collection('users').document(legacy_user_id)
            legacy_doc = legacy_doc_ref.get()
            
            if not legacy_doc.exists:
                return jsonify({"success": False, "message": "Legacy user not found"}), 404
            
            legacy_data = legacy_doc.to_dict()
            print(f"🔍 Migrating legacy user: {legacy_user_id} to Firebase UID: {firebase_uid}")
            
            # Create new user document with Firebase UID
            new_user_data = {
                'user_email': email,
                'user_name': display_name or legacy_data.get('user_name', email.split('@')[0]),
                'firebase_uid': firebase_uid,
                'migrated_from': legacy_user_id,
                'migration_date': datetime.now().isoformat(),
                'created_at': legacy_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            # Copy subscription data if it exists
            if 'subscription_status' in legacy_data:
                new_user_data['subscription_status'] = legacy_data['subscription_status']
            if 'plan' in legacy_data:
                new_user_data['plan'] = legacy_data['plan']
            if 'subscription_start_date' in legacy_data:
                new_user_data['subscription_start_date'] = legacy_data['subscription_start_date']
            if 'stripe_subscription_id' in legacy_data:
                new_user_data['stripe_subscription_id'] = legacy_data['stripe_subscription_id']
            if 'stripe_customer_id' in legacy_data:
                new_user_data['stripe_customer_id'] = legacy_data['stripe_customer_id']
            
            # Create new user document
            new_doc_ref = db.collection('users').document(firebase_uid)
            new_doc_ref.set(new_user_data)
            
            # Mark legacy user as migrated
            legacy_doc_ref.update({
                'migrated_to': firebase_uid,
                'migration_date': datetime.now().isoformat(),
                'migration_status': 'completed'
            })
            
            print(f"🔍 Migration completed: {legacy_user_id} -> {firebase_uid}")
            
            # Update session data
            session['user_id'] = firebase_uid
            session['user_email'] = email
            session['user_name'] = display_name or legacy_data.get('user_name', email.split('@')[0])
            session['firebase_uid'] = firebase_uid
            session['legacy_user'] = False  # No longer a legacy user
            
            # Copy subscription data to session
            if 'subscription_status' in legacy_data:
                session['subscription_status'] = legacy_data['subscription_status']
            if 'plan' in legacy_data:
                session['plan'] = legacy_data['plan']
            if 'subscription_start_date' in legacy_data:
                session['subscription_start_date'] = legacy_data['subscription_start_date']
            if 'stripe_subscription_id' in legacy_data:
                session['stripe_subscription_id'] = legacy_data['stripe_subscription_id']
            if 'stripe_customer_id' in legacy_data:
                session['stripe_customer_id'] = legacy_data['stripe_customer_id']
            
            return jsonify({
                "success": True, 
                "message": "Account successfully migrated to secure authentication!",
                "user_id": firebase_uid,
                "migrated": True
            })
            
        except Exception as e:
            print(f"Error during migration: {e}")
            return jsonify({"success": False, "message": "Migration failed"}), 500
            
    except Exception as e:
        print(f"Migration error: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@application.route("/logout")
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('landing'))

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
    print(f"🔍 Stripe publishable key: {stripe_publishable_key[:20]}...")
    return render_template("payment.html", stripe_publishable_key=stripe_publishable_key)

@application.route("/signup")
def signup():
    """Unified signup and payment page"""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    response = make_response(render_template("signup.html", stripe_publishable_key=stripe_publishable_key))
    return set_no_cache_headers(response)

@application.route("/signup-and-subscribe", methods=["POST"])
def signup_and_subscribe():
    """Handle user signup and subscription creation - PAYMENT FIRST, then create user"""
    print("🚀 SIGNUP-AND-SUBSCRIBE ENDPOINT CALLED!")
    try:
        data = request.get_json()
        print(f"🚀 Received data: {data}")
        user_name = data.get('userName')
        user_email = data.get('userEmail')
        user_password = data.get('userPassword')
        plan = data.get('plan')
        payment_method_id = data.get('payment_method_id')
        print(f"🚀 Extracted: user_name={user_name}, user_email={user_email}, plan={plan}")
        
        if not all([user_name, user_email, user_password, plan, payment_method_id]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        if plan not in ['weekly', 'monthly']:
            return jsonify({"success": False, "message": "Invalid plan"}), 400
        
        # STEP 1: PROCESS PAYMENT FIRST (before creating any user accounts)
        print("💳 STEP 1: Processing payment first...")
        
        # Debug: Check if Stripe is properly configured
        if not stripe.api_key:
            return jsonify({"success": False, "message": "Stripe not configured"}), 500
            
        # Get or create Stripe products and prices
        price_ids = get_or_create_stripe_products()
        if not price_ids:
            return jsonify({"success": False, "message": "Failed to create subscription products"}), 500
        
        price_id = price_ids[plan]
        
        # Create Stripe customer (temporary, will be updated with Firebase UID later)
        customer = stripe.Customer.create(
            email=user_email,
            name=user_name,
            metadata={'user_email': user_email, 'user_name': user_name, 'status': 'pending_firebase_creation'}
        )
        
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer.id,
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            default_payment_method=payment_method_id,
            expand=['latest_invoice.payment_intent'],
            metadata={'user_email': user_email, 'user_name': user_name, 'plan': plan, 'status': 'pending_firebase_creation'}
        )
        
        print(f"💳 Payment processed successfully! Subscription: {subscription.id}, Status: {subscription.status}")
        
        # STEP 2: Only if payment succeeds, create Firebase Auth user
        if subscription.status in ['active', 'trialing']:
            print("✅ STEP 2: Payment successful, creating Firebase Auth user...")
            
            # Create Firebase Auth user
            try:
                # Import Firebase Admin Auth
                from firebase_admin import auth as firebase_auth
                
                # Create user in Firebase Auth
                firebase_user = firebase_auth.create_user(
                    email=user_email,
                    password=user_password,
                    display_name=user_name
                )
                firebase_uid = firebase_user.uid
                print(f"✅ Firebase Auth user created: {firebase_uid}")
                
                # Update Stripe customer with Firebase UID
                stripe.Customer.modify(
                    customer.id,
                    metadata={'user_email': user_email, 'user_name': user_name, 'firebase_uid': firebase_uid, 'status': 'active'}
                )
                
                # Update subscription metadata
                stripe.Subscription.modify(
                    subscription.id,
                    metadata={'user_email': user_email, 'user_name': user_name, 'plan': plan, 'firebase_uid': firebase_uid, 'status': 'active'}
                )
                
            except Exception as e:
                print(f"❌ Failed to create Firebase Auth user: {e}")
                # Cancel the subscription since user creation failed
                stripe.Subscription.delete(subscription.id)
                return jsonify({"success": False, "message": "Failed to create user account"}), 500
        
            # STEP 3: Save to Firestore
            print("💾 STEP 3: Saving user to Firestore...")
            user_id = firebase_uid
            start_date = str(datetime.now())
            
            print(f"🔍 New user signup: {user_name} ({user_email}) with Firebase UID: {firebase_uid}")
            print(f"🔍 Subscription created: {subscription.id}")
            print(f"🔍 Customer ID: {customer.id}")
            
            # Save to Firestore
            print(f"🚀 SAVING TO FIRESTORE: user_id={user_id}, subscription_id={subscription.id}, customer_id={customer.id}")
            success = update_user_subscription(user_id, 'active', plan, start_date, subscription.id, customer.id, user_email, user_name)
            print(f"🚀 FIRESTORE SAVE RESULT: {success}")
            
            if not success:
                print(f"❌❌❌ FAILED TO SAVE USER TO FIRESTORE! User: {user_email}, UID: {user_id}")
                # If Firestore save fails, we should clean up Firebase Auth user and Stripe subscription
                firebase_auth.delete_user(firebase_uid)
                stripe.Subscription.delete(subscription.id)
                return jsonify({"success": False, "message": "Failed to save user data"}), 500
            else:
                print(f"✅✅✅ SUCCESS: USER SAVED TO FIRESTORE! User: {user_email}, UID: {user_id}")
            
            # Set session data
            session['user_id'] = user_id
            session['user_email'] = user_email
            session['user_name'] = user_name
            session['firebase_uid'] = firebase_uid
            session['subscription_status'] = 'active'
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            session['stripe_subscription_id'] = subscription.id
            session['stripe_customer_id'] = customer.id
            
            return jsonify({
                "success": True, 
                "message": "Account created and subscription activated successfully",
                "subscription_id": subscription.id,
                "user_id": user_id,
                "firebase_uid": firebase_uid
            })
        else:
            print(f"❌ Payment failed with status: {subscription.status}")
            return jsonify({"success": False, "message": f"Payment failed: {subscription.status}"}), 400
            
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

@application.route("/test")
def test():
    """Simple test route"""
    return "Test route working!"

@application.route("/test-payment")
def test_payment():
    """Test payment page without authentication"""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    print(f"🔍 Test payment - Stripe publishable key: {stripe_publishable_key[:20]}...")
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
        
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer.id,
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            default_payment_method=payment_method_id,
            expand=['latest_invoice.payment_intent'],
            metadata={'user_id': user_id, 'plan': plan}
        )
        
        if subscription.status in ['active', 'trialing']:
            # Save subscription to Firestore
            start_date = str(datetime.now())
            
            print(f"🔍 Subscription created for user {user_id}, plan: {plan}, subscription_id: {subscription.id}")
            print(f"🔍 Customer ID: {customer.id}")
            
            # Update session
            session['subscription_status'] = 'active'
            session['plan'] = plan
            session['subscription_start_date'] = start_date
            session['stripe_subscription_id'] = subscription.id
            session['stripe_customer_id'] = customer.id
            
            # Save to Firestore
            print(f"🔍 Saving to Firestore: user_id={user_id}, subscription_id={subscription.id}, customer_id={customer.id}")
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
    
    # Get subscription info from Firestore first
    subscription_info = None
    try:
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            stripe_subscription_id = user_data.get('stripe_subscription_id')
            print(f"🔍 Found subscription ID in Firestore: {stripe_subscription_id}")
            
            if stripe_subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    subscription_info = {
                        'id': subscription.id,
                        'status': subscription.status,
                        'current_period_end': getattr(subscription, 'current_period_end', None),
                        'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                        'plan': 'weekly' if 'week' in str(subscription.items) else 'monthly'
                    }
                    print(f"🔍 Subscription info: {subscription_info}")
                except Exception as e:
                    print(f"❌ Error retrieving Stripe subscription: {e}")
            else:
                print(f"❌ No subscription ID found in Firestore for user {user_id}")
        else:
            print(f"❌ User document not found in Firestore: {user_id}")
    except Exception as e:
        print(f"❌ Error getting user from Firestore: {e}")
    
    # Fallback to session if Firestore doesn't have it
    if not subscription_info:
        stripe_subscription_id = session.get('stripe_subscription_id')
        if stripe_subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                subscription_info = {
                    'id': subscription.id,
                    'status': subscription.status,
                    'current_period_end': getattr(subscription, 'current_period_end', None),
                    'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                    'plan': 'weekly' if 'week' in str(subscription.items) else 'monthly'
                }
            except stripe.error.StripeError as e:
                print(f"Error retrieving subscription: {e}")
                subscription_info = None
    
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
        print(f"🔍 No subscription found, redirecting to signup")
        return redirect(url_for('signup'))
    
    print(f"🔍 Subscription found: {subscription_status}, redirecting to main app")
    response = make_response(render_template("index.html"))
    return set_no_cache_headers(response)

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
    """Hardcoded demo analysis for landing page - always shows 'Not Ivy Ready'"""
    data = request.get_json()
    essay_text = data.get('essay', '')
    
    if not essay_text or len(essay_text) < 100:
        return jsonify({"error": "Please provide an essay with at least 100 characters"}), 400
    
    print(f"=== DEMO ANALYZE REQUEST (HARDCODED) ===")
    print(f"Essay length: {len(essay_text)}")
    print(f"Essay preview: {essay_text[:100]}...")
    
    # Simulate AI thinking time (4 seconds)
    import time
    thinking_time = 4
    print(f"Simulating AI analysis for {thinking_time} seconds...")
    time.sleep(thinking_time)
    
    # Hardcoded demo analysis that always shows "Not Ivy Ready"
    demo_analysis = """**Narrative and Storytelling: 65/100**
Your essay shows potential but lacks the compelling narrative structure needed for top-tier applications. The story needs more vivid details and emotional depth to truly engage readers.

**Personal Reflection and Growth: 70/100**
There are glimpses of personal insight, but the reflection could be much deeper. Consider exploring specific moments of growth and transformation that shaped your perspective.

**Unique Voice and Authenticity: 68/100**
While your voice comes through, it needs to be more distinctive. The essay feels somewhat generic and could benefit from more personal anecdotes and unique perspectives.

**Clear Structure and Logical Flow: 72/100**
The basic structure is present, but the flow between ideas could be smoother. Some transitions feel abrupt and the overall organization needs refinement.

**Connection to Larger Themes or Ideas: 65/100**
The connections to broader themes are mentioned but not deeply explored. Consider how your experiences relate to larger societal issues or universal human experiences.

**Intellectual Curiosity: 70/100**
There's evidence of intellectual engagement, but it could be more pronounced. Consider adding more specific examples of how you've pursued knowledge and learning.

**Impact and Initiative: 65/100**
The essay mentions goals and aspirations, but lacks concrete examples of leadership and impact. Consider adding specific instances where you've made a difference.

**Diversity and Global Perspective: 60/100**
The global perspective is limited. Consider how your experiences connect to broader cultural, social, or international contexts.

**Readability and Flow: 75/100**
The writing is generally clear, but some sentences could be more concise and impactful. The overall flow is decent but could be more engaging.

**Uniqueness: 62/100**
The essay covers familiar territory without offering truly unique insights or perspectives. Consider what makes your story different from other applicants.

**Overall Score: 67/100**

**Key Areas for Improvement:**
- Develop a more compelling narrative with specific, vivid details
- Deepen personal reflection and show genuine growth
- Add more unique, personal anecdotes that set you apart
- Strengthen connections to larger themes and global perspectives
- Demonstrate concrete examples of leadership and impact

This essay has potential but needs significant revision to be competitive for top-tier institutions. Focus on developing a more distinctive voice and adding specific examples that illustrate your unique qualities and experiences."""
    
    # Always return "Not Ivy Ready" for demo
    return jsonify({
        "success": True,
        "score": "67",
        "overall_score": "67",
        "ivy_ready": "Not Ivy Ready",
        "strengths": "Shows potential with basic structure and clear writing.",
        "improvements": "Needs more compelling narrative, deeper reflection, and unique personal anecdotes.",
        "full_analysis": demo_analysis,
        "demo": True,
        "message": "This is a preview. Get the full detailed analysis with subscription.",
        "streaming": True
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
    port = int(os.environ.get('PORT', 5000))
    application.run(debug=debug_mode, host='0.0.0.0', port=port)
