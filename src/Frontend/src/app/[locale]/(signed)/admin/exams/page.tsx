import { Suspense } from "react";
import Exams from "@/components/exams/Exams";
import { ErrorBoundary } from "react-error-boundary";
import { examsMetadata } from "@/app/[locale]/setup";
import Loading from "@/components/loading/Loading";

export const metadata = examsMetadata

export default async function ExamsPage() {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <Exams />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
