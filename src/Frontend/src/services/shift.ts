import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { api } from "@/api/api";
import { getURL } from "@/utils";
import { usePaginationStore } from "@/store/pagination";

const AlertInstance = new Alert();

const ENDPOINT_SHIFTS = 'shifts';

export async function getShifts() : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(ENDPOINT_SHIFTS, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getAllShifts() : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_SHIFTS, { page_size: 100 });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getShiftById(id: string) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_SHIFTS}/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createShift(data : any) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_SHIFTS, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.shift_created');
                resolve(response.data);
            }).catch((error: any) => {
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function updateShift(id: string, data: any) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.patch(`${ENDPOINT_SHIFTS}/${id}`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.shift_updated');
                resolve(response.data);
            }).catch((error: any) => {
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function deleteShift(id: string) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.delete(`${ENDPOINT_SHIFTS}/${id}`).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.shift_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.form.delete_shift');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}
