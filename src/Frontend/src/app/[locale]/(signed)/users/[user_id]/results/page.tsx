import Loading from "@/components/loading/Loading";
import UserResults from "@/components/user-results/UserResults";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

export const metadata = {
    title: 'LIA - Results',
    description: 'Results',
}

type TResultsPageProps = {
    params: {
        locale: string,
        user_id: string;
    }
}

export default async function ResultsPage({ params } : TResultsPageProps) {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <UserResults user_id={params.user_id} />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
