import Alert from "@/classes/Alert";
import { ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_EXAMS, ENDPOINT_PROFILE, ENDPOINT_RESULTS, ENDPOINT_USERS } from "@/constants/endpoints";
import { IUserExportResponse, IUsersImportResponse, IProfileResponse, IUserResponse, IUsersResponse } from "@/interfaces/user";
import { abortController, api } from "@/api/api";
import { getURL, simulateRequest } from "@/utils";
import { usePaginationStore } from "@/store/pagination";
import { IExam, IExamResponse, IExamsResponse } from "@/interfaces/exam";
import { IGroup } from "@/interfaces/group";

const AlertInstance = new Alert();

export async function getUsers() : Promise<IUsersResponse> {
    return new Promise<IUsersResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            
            const queryString = window.location.search;
            const urlParams = new URLSearchParams(queryString);
            const params = Object.fromEntries(urlParams);

            const url = getURL(ENDPOINT_USERS, {
                page: pagination.page,
                page_size: pagination.page_size, 
                show_finished: pagination.show_finished, 
                q: pagination.query,
                ...params 
            });

            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR (USER LIST)]: ' + e);
            reject(null);
        }
    });
}

export async function getAllUsers() : Promise<IUsersResponse> {
    return new Promise<IUsersResponse>(async (resolve, reject) => {
        try {
            const endpoint = getURL(ENDPOINT_USERS, { page_size: -1 });
            await api.get(endpoint).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR (USER LIST)]: ' + e);
            reject(null);
        }
    });
}

export async function getUserById(id : string) : Promise<IUserResponse> {
    return new Promise<IUserResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_USERS}/${id}`).then(response => {
                const { data } = response;
                resolve(data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function createUser(data : any) : Promise<IUserResponse> {
    return new Promise<IUserResponse>(async (resolve, reject) => {
        try {
            //const body = getBody(data);
            await api.post(ENDPOINT_USERS, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.user_created');
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(e);
        }
    });
}

export async function updateUserById(id : string, data : any) : Promise<IUserResponse> {
    return new Promise<IUserResponse>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${id}`;
            //const body = getBody(data);
            await api.patch(url, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.user_updated');
                resolve(response.data);
            })
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function deleteUserById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.user_deleted');
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function getProfile() : Promise<IProfileResponse | null> {
    return new Promise<IProfileResponse | null>(async (resolve, reject) => {
        try {
            await api.get(ENDPOINT_PROFILE).then(response => {         
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    })
}

export async function sendImportUsersDataGCS(data : any) : Promise<IUsersImportResponse | null> {
    return new Promise<IUsersImportResponse | null>(async (resolve, reject) => {
        try {
            data.url = data.url.split("?")[0];
            const url = `${ENDPOINT_USERS}/batch`;
            await api.put(url, data).then(response => {         
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    })
}

export async function getExportedUsers() : Promise<IUserExportResponse | null> {
    return new Promise<IUserExportResponse | null>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/export`;
            await api.get(url).then(response => {         
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    })
}

export async function getUsersWithExams() : Promise<IUsersResponse> {
    return new Promise<IUsersResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            
            const queryString = window.location.search;
            const urlParams = new URLSearchParams(queryString);
            const params = Object.fromEntries(urlParams);

            const url = getURL(`${ENDPOINT_USERS}/${ENDPOINT_EXAMS}`, {
                page: pagination.page,
                page_size: pagination.page_size, 
                show_finished: pagination.show_finished, 
                q: pagination.query,
                ...params 
            });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function getAllUsersWithExams(group: string | undefined) : Promise<IUsersResponse> {
    return new Promise<IUsersResponse>(async (resolve, reject) => {
        try {
            let params
            if (group) {
                params = { page_size: -1, groups:group , show_finished: false }
            } else {
                params = { page_size: -1, show_finished: false}
            }

            const endpoint = getURL(`${ENDPOINT_USERS}/${ENDPOINT_EXAMS}`, params);
            await api.get(endpoint).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR (USER LIST)]: ' + e);
            reject(null);
        }
    });
}

export async function getExamsByUserId(user_id: string) : Promise<IExamsResponse> {
    return new Promise<IExamsResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(`${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}`, { 
                page: pagination.page,
                page_size: pagination.page_size, 
                q: pagination.query, 
                show_finished: pagination.show_finished
            });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function getExamsResultsByUserId(user_id: string) : Promise<Array<IExam>> {
    return new Promise<Array<IExam>>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_USERS}/${user_id}/${ENDPOINT_RESULTS}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}

export async function getExamResultByUserId(exam_id: string , user_id: string) : Promise<IExamResponse> {
    return new Promise<IExamResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_EXAMS}/${exam_id}/${ENDPOINT_USERS}/${user_id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            reject(null);
        }
    });
}
