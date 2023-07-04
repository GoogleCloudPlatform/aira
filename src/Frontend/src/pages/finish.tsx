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

