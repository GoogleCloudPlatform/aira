import { examsMetadata } from "@/app/[locale]/setup";
import Loading from "@/components/loading/Loading";
import UserExams from "@/components/user-exams/UserExams";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

export const metadata = examsMetadata

type TUserExamsPageProps = {
    params: {
        locale: string,
        user_id: string;
    }
}

export default async function UserExamsPage({ params } : TUserExamsPageProps) {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <UserExams user_id={params.user_id} />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
