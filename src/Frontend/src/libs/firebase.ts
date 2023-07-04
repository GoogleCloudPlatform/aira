import getConfig from "next/config";
import { getApp, getApps, initializeApp, FirebaseApp } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";

const { publicRuntimeConfig } = getConfig();

const firebaseConfig = {
    apiKey: publicRuntimeConfig.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: publicRuntimeConfig.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: publicRuntimeConfig.NEXT_PUBLIC_FIREBASE_PROJECT_ID,  
    appId: publicRuntimeConfig.NEXT_PUBLIC_FIREBASE_APP_ID,  
};

let firebaseApp: FirebaseApp | null = null;
let auth: Auth | null = null;

if (typeof window !== "undefined") {
    firebaseApp = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    auth = getAuth(firebaseApp);
}

export { auth };