import { cookies } from "next/headers";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { IUser } from "@/interfaces/auth";
import ExamDisplay from "@/components/exam-display/ExamDisplay";
import { examQuestionsMetadata } from "@/app/[locale]/setup";
import Loading from "@/components/loading/Loading";

export const metadata = examQuestionsMetadata

type TExamPageProps = {
    params: Promise<{
        locale: string,
        id: string;
    }>
}

const getUser = async () : Promise<IUser | null> => {
    try {
        const cookieStore = await cookies();
        const user_cookie = cookieStore.get("user");
        if (!user_cookie || !user_cookie.value) return null;
        return JSON.parse(user_cookie.value);
    } catch (error) {
        console.error("[ERROR]: Could not retrieve user");
        return null;
    }
}

export default async function ExamPage({ params } : TExamPageProps) {
    const { id } = await params;
    const user = await getUser();

    if (!user) return <>Could not load informations from user</>

    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <ExamDisplay user_id={user.user_id} exam_id={id} />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
