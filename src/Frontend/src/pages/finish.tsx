import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import type { NextPage } from 'next'
import { ReactElement, ReactNode, useEffect } from 'react';
import { Layout } from '@/layouts';
import { useExamsStore } from '@/store/exams';
import { useRouter } from 'next/router';
import { IExamsStore } from '@/interfaces/store';
import { FinishExam } from '@/components';

type NextPageWithLayout = NextPage & {
    getLayout?: (page: ReactElement) => ReactNode
}

export default function Finish<NextPageWithLayout>() {
    const router = useRouter();

    const { finished, setExams } : IExamsStore = useExamsStore();
  
    if (!finished) router.push("/exams");

    useEffect(() => {
        let ignore = false;

        if (ignore) {
            setExams("finished", false);
        }

        return () => {
            ignore = finished;
        }
    }, [setExams, finished, router]);

    return <FinishExam />
}

Finish.getLayout = function getLayout(page: ReactElement) {
    return (
        <Layout>
            {page}
        </Layout>
    );
}

export async function getServerSideProps({ locale } : any) {
    return {
        props: {
            ...(await serverSideTranslations(locale, ['common', 'exam', 'toast', 'routes'])),
        }
    }
}

