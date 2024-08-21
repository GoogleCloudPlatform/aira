import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_EXAMS, ENDPOINT_QUESTIONS, ENDPOINT_USERS } from "@/constants/endpoints";
import { IExam, IExamResponse, IExamsResponse } from "@/interfaces/exam";
import { api } from "@/api/api";
import { getURL } from "@/utils";
import { usePaginationStore } from "@/store/pagination";

const AlertInstance = new Alert();

export async function getExams() : Promise<IExamsResponse> {
    return new Promise<IExamsResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(ENDPOINT_EXAMS, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
            await api.get(url).then(response => {
                const data : IExamsResponse = response.data;
                resolve(data)
            });
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}

export async function getAllExams() : Promise<IExamsResponse> {
    return new Promise<IExamsResponse>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_EXAMS, { page_size: - 1 });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getExamById(id : string, ) : Promise<IExamResponse> {
    return new Promise<IExamResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_EXAMS}/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            console.error(e);
            AlertInstance.alert(ALERT_ERROR, 'error_api');
            reject(null);
        }
    });
}

export async function createExam(data : any) : Promise<IExamResponse> {
    return new Promise<IExamResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_EXAMS, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.exam_created');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function updateExamById(id : string, data : any) : Promise<IExam> {
    return new Promise<IExam>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_EXAMS}/${id}`;
            await api.patch(url, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.exam_updated');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function deleteExamById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_EXAMS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.exam_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function sendGCSUrl(user_id: string, exam_id: string, question_id: string, gcs_url : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            gcs_url = gcs_url.split("?")[0];
            const url = `${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}/${exam_id}/${ENDPOINT_QUESTIONS}/${question_id}`;
            await api.post(url, { url: gcs_url }).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.exam.success_sent_record');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getExamResultByUserId({ exam_id, user_id } : { exam_id: string, user_id: string }) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_EXAMS}/${exam_id}/from/${user_id}`;
            await api.get(url).then(response => {         
                resolve(response.data);
            })
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getExamQuestionsByUser({ exam_id, user_id } : { exam_id: string, user_id: string }) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}/${exam_id}/${ENDPOINT_QUESTIONS}`;
            await api.get(url).then(response => {         
                resolve(response.data);
            })
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function sendMultipleChoiceAnswer({ exam_id, user_id, question_id, answers } : { exam_id: string, user_id: string, question_id: string, answers: string[] }) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}/${exam_id}/${ENDPOINT_QUESTIONS}/${question_id}`;
            await api.post(url, {answers}).then(response => {       
                resolve(response.data);
            })
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}