# Firebase Credentials Setup Guide

## 🔥 **Setting Up Firebase for Persistent Subscriptions**

To enable persistent subscription storage, you need to set up Firebase credentials.

### **Option 1: Service Account Key (Recommended)**

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Select your project: `ivylab-d0d5e`

2. **Generate Service Account Key**
   - Go to **Project Settings** → **Service Accounts**
   - Click **"Generate new private key"**
   - Download the JSON file

3. **Save the Key File**
   - Rename the downloaded file to: `firebase-service-account.json`
   - Place it in your project root directory: `/Users/nicholasmarcenelle/Desktop/ivybot2/`

4. **Restart the Server**
   ```bash
   python3 application.py
   ```

### **Option 2: Google Cloud CLI (Alternative)**

1. **Install Google Cloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**
   ```bash
   gcloud auth application-default login
   ```

3. **Set Project**
   ```bash
   gcloud config set project ivylab-d0d5e
   ```

4. **Restart the Server**
   ```bash
   python3 application.py
   ```

## ✅ **Verification**

When Firebase is properly configured, you should see:
```
✅ Firebase initialized with service account key
✅ Firestore initialized successfully
```

## 🔧 **Troubleshooting**

### **If you see:**
```
⚠️  Firestore initialization failed: Your default credentials were not found
```

**Solution:** Follow Option 1 or 2 above to set up credentials.

### **If you see:**
```
⚠️  Firestore not available - subscription not persisted
```

**Solution:** Check that your service account key file is in the correct location and has proper permissions.

## 📁 **File Structure**
```
ivybot2/
├── firebase-service-account.json  ← Add this file
├── application.py
├── templates/
└── static/
```

## 🚀 **After Setup**

Once Firebase is configured:
- ✅ Subscriptions persist across logouts
- ✅ User data is stored in Firestore
- ✅ Real-time database updates
- ✅ Scalable cloud storage

Your app will now have persistent subscription storage! 🎉
