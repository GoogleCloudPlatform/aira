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
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alert";
import { ENDPOINT_EXAMS, ENDPOINT_QUESTIONS } from "@/constants/endpoint";
import { IExam, IExamResponse, IExamsResponse } from "@/interfaces/exams";
import { api } from "@/pages/api/api";
import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getExams() : Promise<IExamsResponse> {
    return new Promise<IExamsResponse>(async (resolve, reject) => {
        try {
            await api.get(ENDPOINT_EXAMS).then(response => {
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

export async function getExamById(id : string) : Promise<IExamResponse> {
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
            const body = getBody(data);
            await api.post(ENDPOINT_EXAMS, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'exam_created');
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
            const body = getBody(data);
            await api.patch(url, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'exam_edited');
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
                AlertInstance.alert(ALERT_SUCCESS, 'exam_deleted');
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

export async function sendGCSUrl(exam_id: string, question_id: string, gcs_url : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            gcs_url = gcs_url.split("?")[0];
            const url = `${ENDPOINT_EXAMS}/${exam_id}/${ENDPOINT_QUESTIONS}/${question_id}`;
            await api.post(url, { url: gcs_url }).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'success_sent_record');
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