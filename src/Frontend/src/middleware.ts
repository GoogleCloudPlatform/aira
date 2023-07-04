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
// middleware.ts
import { match } from '@formatjs/intl-localematcher'
import Negotiator from 'negotiator'
import { NextRequest, NextResponse } from 'next/server';
import { i18n } from '../next-i18next.config';

const PUBLIC_FILE = /\.(.*)$/;
const { locales } = i18n;
 
// Get the preferred locale, similar to above or using a library
function getLocale(request : NextRequest) { 
    const acceptLanguage = request.headers.get('accept-language')?.substring(0,5);
    let headers = { 'accept-language': acceptLanguage };
    let languages = new Negotiator({ headers }).languages();
    let defaultLocale = 'en-US';
    
    return match(languages, locales, defaultLocale);
}
 

export async function middleware(req: NextRequest) {
    if (
        req.nextUrl.pathname.startsWith('/_next') ||
        req.nextUrl.pathname.includes('/api/') ||
        PUBLIC_FILE.test(req.nextUrl.pathname)
    ) {
        return;
    }

    if (req.nextUrl.locale === 'default') {
        // Check if there is any supported locale in the pathname
        const pathname = req.nextUrl.pathname
        const pathnameIsMissingLocale = locales.every(
            (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
        )
    
        // Redirect if there is no locale
        if (pathnameIsMissingLocale) {
            const locale = getLocale(req);
            // e.g. incoming request is /
            // The new URL is now /en-US
            return NextResponse.redirect(
                new URL(`/${locale}/${pathname}`, req.url)
            )
        }
    }
}