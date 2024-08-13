import Groups from "@/components/groups/Groups";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { groupsMetadata } from "../../setup";
import Loading from "@/components/loading/Loading";

export const metadata = groupsMetadata

export default async function GroupsPage() {
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <Groups />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
