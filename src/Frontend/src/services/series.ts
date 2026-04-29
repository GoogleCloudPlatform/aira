import { api } from "@/api/api";
import { ENDPOINT_SERIES } from "@/constants/endpoints";
import { getURL } from "@/utils";
import { usePaginationStore } from "@/store/pagination";

export async function getSeries() : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(ENDPOINT_SERIES, { 
                page: pagination.page, 
                page_size: pagination.page_size, 
                q: pagination.query
            });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            reject(null);
        }
    });
}

export async function createSeries(data: any) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_SERIES, data).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            reject(null);
        }
    });
}

export async function updateSeries(id: string, data: any) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.put(`${ENDPOINT_SERIES}/${id}`, data).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            reject(null);
        }
    });
}

export async function deleteSeriesById(id: string) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.delete(`${ENDPOINT_SERIES}/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            reject(null);
        }
    });
}

export async function getSeriesById(id: string) : Promise<any> {
    return new Promise<any>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_SERIES}/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            reject(null);
        }
    });
}
