import { Suspense } from "react";
import ExamDisplay from "@/components/exam-display/ExamDisplay";
import { Blocker } from "@/router/navigation-block/NavigationBlock";
import { ErrorBoundary } from "react-error-boundary";
import { examQuestionsMetadata } from "@/app/[locale]/setup";
import Loading from "@/components/loading/Loading";

export const metadata = examQuestionsMetadata

type TExamPageProps = {
    params: Promise<{
        locale: string,
        user_id: string;
        id: string;
    }>
}

// const fetchData = async ({ user_id, id }: { user_id: string, id: string }) => {
//     const token = cookies().get("token");

//     if (!token || !token.value) {
//         return new Response(JSON.stringify({ error: "No token found" }), { status: 500 });
//     }
  
//     const options = {
//         method: "GET",
//         headers: {
//             "Authorization": `Bearer ${token?.value}`,
//         },
//     };

//     const response = await fetch(`${process.env.NEXT_PUBLIC_APP_API_URL}/users/${user_id}/exams/${id}/questions`, options);
//     const data = await response.json();
//     return data;
// }

export default async function ExamPage({ params } : TExamPageProps) {
    const { user_id, id } = await params;
    //const data = await fetchData({ user_id, id });
    
    return (
        <>
            <article className='flex justify-center items-center w-full h-full overflow-x-hidden overflow-y-auto relative z-10'>
                <div className='flex flex-col gap-4 lg:gap-1 w-full h-full relative pt-5'>
                    <div className="h-full">
                        <ErrorBoundary fallback={<p>⚠️ Something went wrong</p>}>
                            <Suspense fallback={<Loading style="vertical" text={true}/>}>
                                <ExamDisplay user_id={user_id} exam_id={id} />
                                <Blocker />
                            </Suspense>
                        </ErrorBoundary>
                    </div>
                </div>
            </article>
        </>
    );
}
