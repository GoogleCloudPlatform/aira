'use client'

import { createLooker } from '@/libs/looker/looker';
import { LookerEmbedDashboard, LookerEmbedSDK } from '@looker/embed-sdk';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from "react";
import { toast } from 'react-toastify';
import { RBACWrapper } from '@/context/rbac';
import { SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER } from '@/constants/rbac';
import { useTranslations } from 'next-intl';
import Loading from '@/components/loading/Loading';

const Looker : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [dashboardId, setDashboardId] = useState<string>(process.env.NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID || "");
    const [loading, setLoading] = useState<boolean>(true);
    const [hasError, setHasError] = useState<boolean>(false);
    
    const t = useTranslations();
    const router = useRouter();
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
            setHasError(false);
            setLoading(false);  
            const dashboard = document.getElementById("dashboard");
            if (dashboard) dashboard.innerHTML = "";
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
                    toast.error(t("toast.errors.loading.error_loading_looker"));
                    console.error('An unexpected error occurred', error);
                });
        }
    }, [dashboardId, t]);

    // handle route change
    // useEffect(() => {
    //     setDashboardId(process.env.NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID);

    //     return () => {
    //         // clean up looker dashboard
    //         const dashboard = document.getElementById("dashboard");
    //         if (dashboard) dashboard.innerHTML = "";
    //     }
    // }, [mounted, router]);

    if (!mounted) return null;
    if (hasError) return <>⚠️ Something went wrong loading Looker</>;
    

    return (
        <>
            <div className='flex flex-grow justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                {loading ? 
                    <section className='flex w-full h-screen items-center justify-center'>
                        <Loading style="vertical" text={true}/>
                    </section>
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

export default Looker;
