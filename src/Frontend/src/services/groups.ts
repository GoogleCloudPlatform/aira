import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alert";
import { ENDPOINT_GROUPS } from "@/constants/endpoint";
import { IGroup, IGroupResponse, IGroupsResponse } from "@/interfaces/group";
import { api } from "@/pages/api/api";
import { getURL } from "@/utils";
import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getGroups() : Promise<IGroupsResponse> {
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
            const body = getBody(data);
            await api.post(ENDPOINT_GROUPS, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'group_created');
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

export async function updateGroupById(id : string, data : any) : Promise<IGroup> {
    return new Promise<IGroup>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_GROUPS}/${id}`;
            const body = getBody(data);
            await api.patch(url, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'group_edited');
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

export async function deleteGroupById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_GROUPS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'group_deleted');
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