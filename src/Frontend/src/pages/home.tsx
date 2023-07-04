import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import type { NextPage } from 'next'
import { ReactElement, ReactNode, useEffect, useState } from 'react';
import { Layout } from '@/layouts';
import { SCOPE_LEARNER } from '@/constants/rbac';
import { useRouter } from 'next/router';
import { useAuth } from '@/context/auth';

type NextPageWithLayout = NextPage & {
    getLayout?: (page: ReactElement) => ReactNode
}

export default function Home<NextPageWithLayout>() {
    const [mounted, setMounted] = useState<boolean>(false);
    
    const router = useRouter();
    const { user } = useAuth();

    useEffect(() => {
        setMounted(true);

        if (!user || !user.scopes) {
            router.push("/");
            setMounted(false);
        }
            
        const isStudent = user && user.scopes && user.scopes.some(s => [SCOPE_LEARNER].includes(s));
        if (isStudent) router.push("/exams");
        else router.push("/reports");

        return () => setMounted(false);
    }, [user, router])

    if (!mounted) return null;

    return null;
}

Home.getLayout = function getLayout(page: ReactElement) {
    return (
        <Layout>
            {page}
        </Layout>
    );
}

export async function getServerSideProps({ locale } : any) {
    return {
        props: {
            ...(await serverSideTranslations(locale, ['common', 'admin', 'toast', 'routes'])),
        }
    }
}