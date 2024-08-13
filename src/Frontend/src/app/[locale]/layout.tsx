//"use client"; // keep track of issue https://github.com/vercel/next.js/issues/48879 causing a flick on components
 
import { Inter } from 'next/font/google'
import { Locale, getMessages } from '../../libs/i18n/i18n-config';
import App from '@/components/app/App';
import { NextIntlClientProvider } from 'next-intl';
import { notFound } from 'next/navigation';
import { Metadata } from 'next';
import { BlockBrowserNavigation, NavigationBlockerProvider } from '@/router/navigation-block/NavigationBlock';
import { appMetadata } from './setup';

export const metadata : Metadata = appMetadata

const inter = Inter({ subsets: ['latin'] });

export default async function RootLayout({ children, params: { locale } }: { children: React.ReactNode, params: { locale: string } }) {
    let messages;
    try {
        messages = await getMessages(locale as Locale);
    } catch (error) {
        console.error('[ERROR PARSING MESSAGES]', error);
        notFound();
    }

    return (
        <html lang={locale} suppressHydrationWarning={true}>
            <body className={inter.className} style={{ height: "100vh", overflow: "hidden" }}>
                <NextIntlClientProvider locale={locale} messages={messages}>
                    <App>
                        <NavigationBlockerProvider>
                            {/* Blocks reloading the page / navigating away to other urls */}
                            <BlockBrowserNavigation />
                            {/* <BlockBrowserBackNavigation />  */}
                            {children}
                        </NavigationBlockerProvider>
                    </App>
                </NextIntlClientProvider>
            </body>
        </html>
    )
}
