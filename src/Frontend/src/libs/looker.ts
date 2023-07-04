import { ENDPOINT_AUTH_LOOKER } from "@/constants/endpoint";
import { LookerEmbedSDK } from "@looker/embed-sdk";
import getConfig from "next/config";

const { publicRuntimeConfig } = getConfig();

export function createLooker() {
    try {
        if (typeof window !== "undefined") {
            LookerEmbedSDK.init(publicRuntimeConfig.NEXT_PUBLIC_LOOKER,   {
                url: publicRuntimeConfig.NEXT_PUBLIC_API_URL + ENDPOINT_AUTH_LOOKER,
                headers: [{'name': 'Authorization', 'value': `Bearer ${localStorage.getItem("token")}`}],
                withCredentials: true // Needed for CORS requests to Auth endpoint include Http Only cookie headers
            });
        }
    } catch (error) {
        console.error(error);
    }
}
