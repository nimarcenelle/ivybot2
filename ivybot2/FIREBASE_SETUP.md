# Firebase Authentication Setup Guide

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter project name: "IvyLab" (or your preferred name)
4. Enable Google Analytics (optional)
5. Click "Create project"

## 2. Add Web App to Firebase

1. In your Firebase project, click the web icon `</>`
2. Enter app nickname: "IvyLab Web"
3. Check "Also set up Firebase Hosting" (optional)
4. Click "Register app"
5. Copy the Firebase configuration object

## 3. Update Configuration

1. Open `templates/auth.html`
2. Find the `firebaseConfig` object (around line 20)
3. Replace the placeholder values with your actual Firebase config:

```javascript
const firebaseConfig = {
    apiKey: "your-actual-api-key",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "your-actual-sender-id",
    appId: "your-actual-app-id"
};
```

## 4. Enable Authentication

1. In Firebase Console, go to "Authentication"
2. Click "Get started"
3. Go to "Sign-in method" tab
4. Enable "Email/Password" provider
5. Configure any additional settings as needed

## 5. Set Environment Variables

1. Create a `.env` file in your project root
2. Add your secret key and Firebase service account:

```
SECRET_KEY=your-super-secret-key-here
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id",...}
```

**OR** create a `firebase-service-account.json` file locally (this file is gitignored and won't be committed):
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

## 6. Test the Authentication

1. Start your Flask app: `python3 application.py`
2. Visit `http://localhost:5004/auth`
3. Try creating an account and signing in
4. Test the logout functionality

## Features Included

- ✅ Email/Password authentication
- ✅ Session management
- ✅ Protected routes
- ✅ User-friendly error messages
- ✅ Responsive design matching your app

## Security Notes

- The Firebase config is safe to include in client-side code
- User authentication is handled by Firebase
- Sessions are managed server-side
- All sensitive operations require authentication
- **IMPORTANT**: Never commit `firebase-service-account.json` to version control
- Use environment variables for production deployments
- The service account file is automatically gitignored

## Troubleshooting

- Make sure your Firebase project has Authentication enabled
- Check that your domain is authorized in Firebase Console
- Verify your API keys are correct
- Check browser console for any JavaScript errors
