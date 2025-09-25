// Firebase Configuration
// Replace these values with your actual Firebase project configuration
// You can find these in your Firebase Console > Project Settings > General

export const firebaseConfig = {
    apiKey: "your-api-key-here",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};

// Instructions to set up Firebase:
// 1. Go to https://console.firebase.google.com/
// 2. Create a new project or select existing project
// 3. Go to Project Settings > General
// 4. Scroll down to "Your apps" section
// 5. Click "Add app" and select Web
// 6. Copy the config values and replace the ones above
// 7. Enable Authentication in Firebase Console:
//    - Go to Authentication > Sign-in method
//    - Enable Email/Password
//    - Enable Google (optional)
// 8. Update the auth.html file with your actual config values
