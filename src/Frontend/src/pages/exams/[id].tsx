import useSWR from 'swr';
import { ENDPOINT_EXAMS } from '@/constants/endpoint';
import { Layout } from '@/layouts';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useRouter } from 'next/router';
import { ReactElement, useEffect } from 'react';
import { api } from '../api/api';
import { useExamsStore } from '@/store/exams';
import { IExamsStore } from '@/interfaces/store';
import { Exam, NoData } from '@/components';
import { RBACWrapper } from '@/context/rbac';
import { SCOPE_LEARNER } from '@/constants/rbac';
import { ShimmerExam } from '@/components/shimmer';

export default function Page() {
    const router = useRouter();

    const { exam, setExams } : IExamsStore = useExamsStore();
    const { data, error, isLoading } : any = useSWR(`${ENDPOINT_EXAMS}/${router.query.id}/questions`, api, { revalidateIfStale: false, revalidateOnFocus: false, revalidateOnMount: true });

    useEffect(() => {
        if (data) setExams("exam", data.data)
    }, [data, setExams]);
    
    if (!exam) return <NoData />;
    if (isLoading) return <ShimmerExam />
    if (error) return <NoData message='error_load_exam' />;

    return (
        <RBACWrapper requiredScopes={[SCOPE_LEARNER]}>
            <Exam exam={exam} />
        </RBACWrapper>
    );
}

Page.getLayout = function getLayout(page: ReactElement) {
    return (
        <Layout>
            {page}
        </Layout>
    );
}

export async function getServerSideProps({ locale } : any) {
    return {
        props: {
            ...(await serverSideTranslations(locale, ['common', 'modal', 'exam', 'toast', 'routes'])),
        }
    }
}
