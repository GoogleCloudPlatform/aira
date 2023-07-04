import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import type { NextPage } from 'next'
import { ReactElement, ReactNode, useEffect, useState } from 'react';
import { Layout } from '@/layouts';
import { Exams } from '@/components';

type NextPageWithLayout = NextPage & {
    getLayout?: (page: ReactElement) => ReactNode
}

export default function Page<NextPageWithLayout>() {    
    return (
        <div className='flex justify-center items-center p-2 md:p-10 w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
            <Exams />
        </div>
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
            ...(await serverSideTranslations(locale, ['common', 'modal', 'fields', 'toast', 'routes', 'exam'])),
        }
    }
}

