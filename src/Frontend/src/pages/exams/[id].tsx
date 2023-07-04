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
