// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
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