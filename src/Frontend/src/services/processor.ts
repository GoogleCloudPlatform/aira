import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alerts";
import { ENDPOINT_PROCESSOR_SIGNED } from "@/constants/endpoints";
import { IProcessorSignedResponse } from "@/interfaces/processor";
import { api } from "@/api/api";

const AlertInstance = new Alert();

export async function getProcessorSignedLink(exam_id : string, user_id: string, question_id: string, mime_type: string) : Promise<IProcessorSignedResponse> {
    return new Promise<IProcessorSignedResponse>(async (resolve, reject) => {
        try {
            const file_type = mime_type.split("/")[1];
            await api.post(ENDPOINT_PROCESSOR_SIGNED, { exam_id, user_id, question_id, file_type, mimetype: mime_type }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}

export async function getProcessorImportSignedLink(type: string, mime_type: string) : Promise<IProcessorSignedResponse> {
    return new Promise<IProcessorSignedResponse>(async (resolve, reject) => {
        try {
            const file_type = mime_type.split("/")[1];
            await api.post(ENDPOINT_PROCESSOR_SIGNED, { type, file_type, mimetype: mime_type }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}