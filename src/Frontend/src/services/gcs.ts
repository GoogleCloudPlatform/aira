import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alerts";
import { isEmpty } from "lodash";

const AlertInstance = new Alert();

export async function uploadToGCS(url: string, file : any, mime_type: string) : Promise<Boolean | string> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const xhttp = new XMLHttpRequest();
            //Send the proper header information along with the request
            xhttp.open("PUT", url, true);

            xhttp.setRequestHeader('Content-type', mime_type);
            
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    // Typical action to be performed when the document is ready:
                    const response = !isEmpty(this.responseURL) ? this.responseURL : true;
                    resolve(response);
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