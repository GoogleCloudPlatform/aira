import { ENDPOINT_AUTH_LOOKER } from "@/constants/endpoints";
import { getCookie } from "@/utils/auth";
import { LookerEmbedSDK } from "@looker/embed-sdk";

export function createLooker() {
    try {
        if (typeof window !== "undefined") {
            const looker = process.env.NEXT_PUBLIC_LOOKER;
            const token = getCookie("token");
            if (!looker || !token) return;
            LookerEmbedSDK.init(looker,   {
                url: process.env.NEXT_PUBLIC_API_URL + ENDPOINT_AUTH_LOOKER,
                headers: [{'name': 'Authorization', 'value': `Bearer ${localStorage.getItem("token")}`}],
                withCredentials: true // Needed for CORS requests to Auth endpoint include Http Only cookie headers
            });
        }
    } catch (error) {
        console.error(error);
    }
}
