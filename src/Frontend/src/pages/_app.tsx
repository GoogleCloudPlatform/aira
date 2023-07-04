import '@/styles/globals.css'
import { ReactElement, ReactNode, Suspense } from 'react';
import type { NextPage } from 'next';
import type { AppProps } from 'next/app'
import { appWithTranslation } from 'next-i18next';
import Head from 'next/head';
import { AuthProvider, ProtectRoute  } from '@/context/auth';
import { GlobalLoading, Toast } from '@/components';

import { ROLES, SCOPES } from '@/constants/rbac';
import { RBACProvider } from '@/context/rbac';

type NextPageWithLayout = NextPage & {
    getLayout?: (page: ReactElement) => ReactNode
}

type AppPropsWithLayout = AppProps & {
    Component: NextPageWithLayout
}

function MyApp({ Component, pageProps: { session, ...pageProps } }: AppPropsWithLayout) {

    const getLayout = Component.getLayout ?? ((page) => page);

    const app = (
        <>
            <Head>
                <meta name='viewport' content='minimum-scale=1, initial-scale=1, width=device-width, shrink-to-fit=no, maximum-scale=5, viewport-fit=cover' /> 
                <link rel="manifest" href="/manifest.json" />
            </Head>
            <Suspense fallback={<div>Loading...</div>}>
                <AuthProvider>
                    <ProtectRoute>
                        <RBACProvider roles={ROLES} scopes={SCOPES}>
                            {getLayout(<Component {...pageProps} />)}
                        </RBACProvider>
                    </ProtectRoute>
                </AuthProvider>
            </Suspense>
            <Toast />
            <GlobalLoading />
        </>
    );

    return app;
}

export default appWithTranslation(MyApp);