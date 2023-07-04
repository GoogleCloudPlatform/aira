import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import type { NextPage } from 'next'
import { ReactElement, ReactNode, useEffect } from 'react';
import { SigninLayout } from '@/layouts';
import SignIn from '@/components/signin/Signin';

type NextPageWithLayout = NextPage & {
    getLayout?: (page: ReactElement) => ReactNode
}

export default function Signin<NextPageWithLayout>() {

    useEffect(() => {
        const clearSession = () => {
            localStorage.clear();
            sessionStorage.clear();
        }

        clearSession();
    }, []);

    return (
        <>
            <SignIn />
        </>
    );
}

Signin.getLayout = function getLayout(page: ReactElement) {
    return (
        <SigninLayout>
            {page}
        </SigninLayout>
    );
}

export async function getServerSideProps({ locale } : any) {
    return {
        props: {
            ...(await serverSideTranslations(locale, ['common', 'signin', 'toast', 'routes'])),
        }
    }
}

