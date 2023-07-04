import { Exams, Groups, Organizations, Roles, Users } from '@/components';
import Search from '@/components/search/Search';
import { EXAMS, GROUPS, ORGANIZATIONS, ROLES, USERS } from '@/constants/pages';
import { Layout } from '@/layouts';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useRouter } from 'next/router';
import { ReactElement } from 'react';
 
export default function Page() {
    const router = useRouter();
    
    if (!router.query.slug) return null;
    const component = router.query.slug[0];

    const getComponent = (path : string) => {
        if (path === ORGANIZATIONS) return <Organizations />
        if (path === GROUPS) return <Groups />
        if (path === ROLES) return <Roles />
        if (path === EXAMS) return <Exams />
        if (path === USERS) return <Users />

        return null;
    }

    return (
        <>
            <div className='flex justify-center items-center p-2 md:p-10 w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-2 w-full h-full'>
                    <div className='w-full sm:w-80'>
                        <Search />
                    </div>
                    {getComponent(component)}
                </div>
            </div>
        </>
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
            ...(await serverSideTranslations(locale, ['common', 'admin', 'fields', 'modal', 'toast', 'routes'])),
        }
    }
}