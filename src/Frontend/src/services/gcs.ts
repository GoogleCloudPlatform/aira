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
import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alert";

const AlertInstance = new Alert();

export async function uploadToGCS(url: string, file : any, mime_type: string) : Promise<Boolean> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const xhttp = new XMLHttpRequest();
            //Send the proper header information along with the request
            xhttp.open("PUT", url, true);

            xhttp.setRequestHeader('Content-type', mime_type);
            
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    // Typical action to be performed when the document is ready:
                    resolve(true);
                }
            };

            xhttp.onerror = function() {
                reject(false)
            }
            
            xhttp.send(file);  /* Send to server */ 
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(false);
        }
    });
}