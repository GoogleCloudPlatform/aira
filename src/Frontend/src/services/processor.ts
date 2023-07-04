import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alert";
import { ENDPOINT_PROCESSOR_SIGNED } from "@/constants/endpoint";
import { IProcessorSignedResponse } from "@/interfaces/processor";
import { api } from "@/pages/api/api";

const AlertInstance = new Alert();

export async function getProcessorSignedLink(exam_id : string, question_id: string, mime_type: string) : Promise<IProcessorSignedResponse> {
    return new Promise<IProcessorSignedResponse>(async (resolve, reject) => {
        try {
            const file_type = mime_type.split("/")[1];
            api.post(ENDPOINT_PROCESSOR_SIGNED, { exam_id, question_id, file_type, mimetype: mime_type }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}