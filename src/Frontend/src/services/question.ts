import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alert";
import { ENDPOINT_EXAMS } from "@/constants/endpoint";
import { IQuestion, IQuestionResponse } from "@/interfaces/question";
import { api } from "@/pages/api/api";

const AlertInstance = new Alert();

export async function getQuestionById(id : string) : Promise<IQuestionResponse> {
    return new Promise<IQuestionResponse>(async (resolve, reject) => {
        try {
            const data : IQuestionResponse = {
             
            }
            resolve(data);
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}