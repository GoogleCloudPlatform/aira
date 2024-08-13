import { FirebaseApp, getApp, getApps, initializeApp } from "firebase/app";
import { Analytics, getAnalytics, isSupported } from "firebase/analytics";
import { Auth, getAuth } from "firebase/auth";

let firebaseApp : FirebaseApp | null = null;
let auth : Auth | null = null;
let analytics : Analytics | null = null;

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    // storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    // messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGE_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    //measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID
};

if (typeof window !== "undefined") {
    firebaseApp = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    auth = getAuth(firebaseApp);
    // verify if scope has analytics support (jest tests)
    isSupported().then(hasAnalytics => {
        if (hasAnalytics) {
            analytics = getAnalytics(firebaseApp as FirebaseApp);
        }
    });
}

export { auth, analytics };