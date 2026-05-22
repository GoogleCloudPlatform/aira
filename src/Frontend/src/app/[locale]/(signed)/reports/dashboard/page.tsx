import { reportsMetadata } from "@/app/[locale]/setup";
import Loading from "@/components/loading/Loading";
import Dashboard from "@/components/dashboard/Dashboard";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { RBACWrapper } from "@/context/rbac";
import { SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER, SCOPE_EXAM_LIST } from "@/constants/rbac";

export const metadata = reportsMetadata

export default async function DashboardPage() {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full w-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong loading the dashboard</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <RBACWrapper requiredScopes={[SCOPE_ADMIN, SCOPE_DASHBOARD_VIEWER, SCOPE_EXAM_LIST]}>
                                    <Dashboard />
                                </RBACWrapper>
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}

