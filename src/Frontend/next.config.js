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
/** @type {import('next').NextConfig} */

const runtimeCaching = require('next-pwa/cache');
const { i18n } = require('./next-i18next.config');

const withPWA = require('next-pwa')({
    disable: process.env.NODE_ENV === "development",
    dest: "public",
    register: true,
    skipWaiting: true,
    runtimeCaching,
});

const nextConfig = withPWA({
    //chunks: true,
    swcMinify: true, 
    reactStrictMode: true,
    i18n,
    publicRuntimeConfig: {
        NEXT_PUBLIC_API_URL: process.env.API_URL,
        NEXT_PUBLIC_FIREBASE_API_KEY: process.env.FIREBASE_API_KEY,
        NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.FIREBASE_AUTH_DOMAIN,
        NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.FIREBASE_PROJECT_ID,
        NEXT_PUBLIC_FIREBASE_APP_ID: process.env.FIREBASE_APP_ID,
        NEXT_PUBLIC_LOOKER: process.env.LOOKER,
        NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID: process.env.LOOKER_GENERAL_DASHBOARD_ID,
        NEXT_PUBLIC_LOOKER_LEARNERS_DASHBOARD_ID: process.env.LOOKER_LEARNERS_DASHBOARD_ID,
    },
});

module.exports = nextConfig;
