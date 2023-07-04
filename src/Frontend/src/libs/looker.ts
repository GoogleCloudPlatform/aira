// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
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
