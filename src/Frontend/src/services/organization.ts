import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_ORGANIZATIONS } from "@/constants/endpoints";
import { IOrganization, IOrganizationExportResponse, IOrganizationsImportResponse, IOrganizationResponse, IOrganizationsResponse, IOrganizationsUtilsResponse } from "@/interfaces/organization";
import { api } from "@/api/api";
import { getURL } from "@/utils";
import { SchemaCreateOrganization, SchemaEditOrganization } from "@/forms/organization/schema";
import { z } from "zod";
import { usePaginationStore } from "@/store/pagination";
//import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getOrganizations() : Promise<IOrganizationsResponse> {
    return new Promise<IOrganizationsResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(ENDPOINT_ORGANIZATIONS, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getAllOrganizations() : Promise<IOrganizationsResponse> {
    return new Promise<IOrganizationsResponse>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_ORGANIZATIONS, { page_size: - 1 });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getOrganizationById(id : string) : Promise<IOrganizationResponse> {
    return new Promise<IOrganizationResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_ORGANIZATIONS}/${id}`).then(response => {
                const { data } = response;
                resolve(data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createOrganization(data : z.infer<typeof SchemaCreateOrganization>) : Promise<IOrganizationResponse> {
    return new Promise<IOrganizationResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_ORGANIZATIONS, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.organization_created');
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

export async function updateOrganizationById(id : string, data : z.infer<typeof SchemaEditOrganization>) : Promise<IOrganization> {
    return new Promise<IOrganization>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ORGANIZATIONS}/${id}`;
            await api.patch(url, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.organization_updated');
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

export async function deleteOrganizationById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ORGANIZATIONS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.organization_deleted');
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

export async function getOrganizationsUtils() : Promise<IOrganizationsUtilsResponse> {
    return new Promise<IOrganizationsUtilsResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_ORGANIZATIONS}/utils`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function sendImportOrganizationsDataGCS(data : any) : Promise<IOrganizationsImportResponse | null> {
    return new Promise<IOrganizationsImportResponse | null>(async (resolve, reject) => {
        try {
            data.url = data.url.split("?")[0];
            const url = `${ENDPOINT_ORGANIZATIONS}/batch`;
            await api.put(url, data).then(response => {         
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getExportedOrganizations() : Promise<IOrganizationExportResponse | null> {
    return new Promise<IOrganizationExportResponse | null>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ORGANIZATIONS}/export`;
            await api.get(url).then(response => {       
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}