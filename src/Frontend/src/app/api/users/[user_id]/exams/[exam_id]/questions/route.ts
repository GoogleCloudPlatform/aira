import { ENDPOINT_EXAMS, ENDPOINT_USERS } from "@/constants/endpoints";
import { usePaginationStore } from "@/store/pagination";
import { getURL } from "@/utils"
import { cookies, headers } from "next/headers";

export async function GET(request: Request, { params }: { params: { user_id: string, exam_id: string }}) {
    // const { searchParams } = new URL(request.url);
    // const user_id = searchParams.get('user_id');
    const user_id = params.user_id;
    const exam_id = params.exam_id;
    const pagination = usePaginationStore.getState();
    const endpoint = getURL(`${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}/${exam_id}/questions`, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
    const url = process.env.NEXT_PUBLIC_API_URL + endpoint;
    
    const headersList = headers();
    const authorization = headersList.get('authorization')
    if (!authorization) {
        return new Response(JSON.stringify({ error: "No token found" }), { status: 500 });
    }
  
    const options = {
        method: "GET",
        headers: {
            "Authorization": authorization,
        },
    };
  
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(await response.text());
        }
        // Parse the JSON response
        const responseData = await response.json();
        return new Response(JSON.stringify(responseData));
    } catch (error: any) {
        console.error("Error:", error.message);
        // Handle the error and create a response accordingly
        return new Response(JSON.stringify({ error: error.message }), { status: 500 });
    }
}
  