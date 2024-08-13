import { api } from "@/api/api";
import { getURL } from "@/utils";
import { usePaginationStore } from "@/store/pagination";
import { IGroup, IGroupExportResponse, IGroupResponse, IGroupsImportResponse, IGroupsResponse } from "@/interfaces/group";
import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_GROUPS } from "@/constants/endpoints";

const AlertInstance = new Alert();

export async function getGroups() : Promise<IGroupsResponse> {
    return new Promise<IGroupsResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(ENDPOINT_GROUPS, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getAllGroups() : Promise<IGroupsResponse> {
    return new Promise<IGroupsResponse>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_GROUPS, { page_size: - 1 });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getGroupById(id : string) : Promise<IGroupResponse> {
    return new Promise<IGroupResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_GROUPS}/${id}`).then(response => {
                const { data } = response;
                resolve(data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createGroup(data : any) : Promise<IGroupResponse> {
    return new Promise<IGroupResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_GROUPS, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.group_created');
                resolve(response.data);
            }).catch((error: any) => {
                //AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function updateGroupById(id : string, data : any) : Promise<IGroup> {
    return new Promise<IGroup>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_GROUPS}/${id}`;
            await api.patch(url, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.group_updated');
                resolve(response.data);
            }).catch((error: any) => {
                //AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function deleteGroupById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_GROUPS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.group_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                //AlertInstance.alert(ALERT_ERROR, 'error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function sendImportGroupsDataGCS(data : any) : Promise<IGroupsImportResponse | null> {
    return new Promise<IGroupsImportResponse | null>(async (resolve, reject) => {
        try {
            data.url = data.url.split("?")[0];
            const url = `${ENDPOINT_GROUPS}/batch`;
            await api.put(url, data).then(response => {         
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    })
}

export async function getExportedGroups() : Promise<IGroupExportResponse | null> {
    return new Promise<IGroupExportResponse | null>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_GROUPS}/export`;
            await api.get(url).then(response => { 
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    })
}