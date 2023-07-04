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
import { DASHBOARD } from '@/constants/pages';
import { Layout } from '@/layouts';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useRouter } from 'next/router';
import { ReactElement, useCallback, useEffect, useState } from 'react';
import { LookerEmbedDashboard, LookerEmbedSDK } from '@looker/embed-sdk';
import { Loading, NoData } from '@/components';
import { ANIMATION_SPIN } from '@/constants/animation';
import { RBACWrapper } from '@/context/rbac';
import { SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER } from '@/constants/rbac';
import getConfig from 'next/config';
import { toast } from 'react-toastify';
import { createLooker } from '@/libs/looker';
import { i18n } from 'next-i18next';


const { publicRuntimeConfig } = getConfig();
 
export default function Page() {
    const router = useRouter();
    
    const [dashboardId, setDashboardId] = useState<number>(router.query && router.query.slug && router.query.slug[0] === DASHBOARD ? 
        publicRuntimeConfig.NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID : publicRuntimeConfig.NEXT_PUBLIC_LOOKER_LEARNERS_DASHBOARD_ID);
    const [loading, setLoading] = useState<boolean>(true);
    const [hasError, setHasError] = useState<boolean>(false);
    const [mounted, setMounted] = useState<boolean>(false);

    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
            setHasError(false);
            setLoading(false);  
        }
    }, []);
 
    const LookDiv = useCallback((el : HTMLDivElement) => {
        if (el) {
            if (el.hasChildNodes()) return;
            
            setLoading(true);
            createLooker();

            LookerEmbedSDK.createDashboardWithId(dashboardId)
                .withClassName("w-full", 'h-full')
                .withAllowAttr('fullscreen')
                .appendTo(el)
                .on('dashboard:run:start',
                    () => {
                        console.log("[Looker] running") 
                    }
                )
                .on('dashboard:run:complete',
                    () => {
                        console.log("[Looker] done")
                        setLoading(false)
                    }
                )
                .build()
                .connect()
                .then((dashboard : LookerEmbedDashboard) => dashboard.send('dashboard:run'))
                .catch((error: Error) => {
                    setHasError(true);
                    setLoading(false);
                    toast.error(i18n?.t("error_loading_looker", { ns: "toast" }));
                    console.error('An unexpected error occurred', error);
                });
        }
    }, [dashboardId]);

    // handle route change
    useEffect(() => {
        if (router.query && router.query.slug && router.query.slug[0] === DASHBOARD) {
            setDashboardId(publicRuntimeConfig.NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID);
        } else {
            setDashboardId(publicRuntimeConfig.NEXT_PUBLIC_LOOKER_LEARNERS_DASHBOARD_ID);
        }

        return () => {
            // clean up looker dashboard
            const dashboard = document.getElementById("dashboard");
            if (dashboard) dashboard.innerHTML = "";
        }
    }, [mounted, router]);

    if (!mounted) return null;
    if (hasError) return <NoData />;
    

    return (
        <>
            <div className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                {loading ? 
                    <div className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                        <div className='w-full h-full bg-gray-300 animate-pulse flex items-center justify-center text-black'>
                            <Loading animation={ANIMATION_SPIN} size={12} />
                        </div>
                    </div>
                    : 
                    null
                }
                <RBACWrapper requiredScopes={[SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER]}>
                    <div id="dashboard" ref={LookDiv} className='w-full h-full' style={{ display: loading ? 'none' : 'block' }}></div>                    
                </RBACWrapper>
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