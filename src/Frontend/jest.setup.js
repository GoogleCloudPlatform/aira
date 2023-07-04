// Optional: configure or set up a testing framework before each test.
// If you delete this file, remove `setupFilesAfterEnv` from `jest.config.js`

// Used for __tests__/testing-library.js
// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/extend-expect'
// The below can be used in a Jest global setup file or similar for your testing set-up
import { loadEnvConfig } from '@next/env';


loadEnvConfig(process.cwd());

jest.mock('next/config', () => () => ({
    publicRuntimeConfig: { // put test stuff here 
        NEXT_PUBLIC_API_URL: process.env.API_URL,
        NEXT_PUBLIC_FIREBASE_API_KEY: process.env.FIREBASE_API_KEY,
        NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.FIREBASE_AUTH_DOMAIN,
        NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.FIREBASE_PROJECT_ID,
        NEXT_PUBLIC_FIREBASE_APP_ID: process.env.FIREBASE_APP_ID,
        NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: process.env.FIREBASE_MEASUREMENT_ID
    },
}));