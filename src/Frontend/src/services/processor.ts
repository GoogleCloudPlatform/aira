import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alerts";
import { ENDPOINT_PROCESSOR_SIGNED } from "@/constants/endpoints";
import { IProcessorSignedResponse } from "@/interfaces/processor";
import { api } from "@/api/api";

const AlertInstance = new Alert();

const AUDIO_MIME_TO_FILE_TYPE: Record<string, string> = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/webm": "webm",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
};

const IMPORT_MIME_TO_FILE_TYPE: Record<string, string> = {
    "text/csv": "csv",
};

export async function getProcessorSignedLink(exam_id : string, user_id: string, question_id: string, mime_type: string) : Promise<IProcessorSignedResponse> {
    return new Promise<IProcessorSignedResponse>(async (resolve, reject) => {
        try {
            const file_type = AUDIO_MIME_TO_FILE_TYPE[mime_type];
            if (!file_type) {
                throw new Error(`Unsupported audio MIME type: ${mime_type}`);
            }
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
            const file_type = IMPORT_MIME_TO_FILE_TYPE[mime_type];
            if (!file_type) {
                throw new Error(`Unsupported import MIME type: ${mime_type}`);
            }
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