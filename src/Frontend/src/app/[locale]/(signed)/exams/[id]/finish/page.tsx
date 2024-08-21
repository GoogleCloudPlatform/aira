import { examFinishMetadata } from "@/app/[locale]/setup";
import ExamDisplay from "@/components/exam-display/ExamDisplay";
import ExamFinish from "@/components/exam-finish/ExamFinish";
import Loading from "@/components/loading/Loading";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

export const metadata = examFinishMetadata

type TExamFinishPageProps = {
    params: {
        locale: string,
        id: string;
    }
}

export default async function ExamFinishPage({ params } : TExamFinishPageProps) {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10 text-black dark:text-white'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <ExamFinish />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
