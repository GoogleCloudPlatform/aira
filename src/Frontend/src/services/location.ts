import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_LOCATIONS } from "@/constants/endpoints";
import { ICountry, ICountriesResponse, ICountryResponse, IState, IStatesResponse, IStateResponse, ICity, ICitiesResponse, ICityResponse } from "@/interfaces/location";
import { api } from "@/api/api";
import { getURL } from "@/utils";
import { usePaginationStore } from "@/store/pagination";

const AlertInstance = new Alert();

// Countries

export async function getCountries() : Promise<ICountriesResponse> {
    return new Promise<ICountriesResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(`${ENDPOINT_LOCATIONS}/countries`, { page: pagination.page, page_size: pagination.page_size, q: pagination.query });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getCountryById(id : string) : Promise<ICountryResponse> {
    return new Promise<ICountryResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_LOCATIONS}/countries/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createCountry(data : any) : Promise<ICountryResponse> {
    return new Promise<ICountryResponse>(async (resolve, reject) => {
        try {
            await api.post(`${ENDPOINT_LOCATIONS}/countries`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.country_created');
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

export async function updateCountryById(id : string, data : any) : Promise<ICountry> {
    return new Promise<ICountry>(async (resolve, reject) => {
        try {
            await api.put(`${ENDPOINT_LOCATIONS}/countries/${id}`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.country_updated');
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

export async function deleteCountryById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            await api.delete(`${ENDPOINT_LOCATIONS}/countries/${id}`).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.country_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.form.delete_country');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

// States

export async function getStates(page: number = 1, countryId?: string) : Promise<IStatesResponse> {
    return new Promise<IStatesResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(`${ENDPOINT_LOCATIONS}/states`, { 
                page: page, 
                page_size: pagination.page_size, 
                q: pagination.query,
                country_id: countryId
            });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getStateById(id : string) : Promise<IStateResponse> {
    return new Promise<IStateResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_LOCATIONS}/states/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createState(data : any) : Promise<IStateResponse> {
    return new Promise<IStateResponse>(async (resolve, reject) => {
        try {
            await api.post(`${ENDPOINT_LOCATIONS}/states`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.state_created');
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

export async function updateStateById(id : string, data : any) : Promise<IState> {
    return new Promise<IState>(async (resolve, reject) => {
        try {
            await api.put(`${ENDPOINT_LOCATIONS}/states/${id}`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.state_updated');
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

export async function deleteStateById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            await api.delete(`${ENDPOINT_LOCATIONS}/states/${id}`).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.state_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.form.delete_state');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

// Cities

export async function getCities(stateId?: string) : Promise<ICitiesResponse> {
    return new Promise<ICitiesResponse>(async (resolve, reject) => {
        try {
            const pagination = usePaginationStore.getState();
            const url = getURL(`${ENDPOINT_LOCATIONS}/cities`, { 
                page: pagination.page, 
                page_size: pagination.page_size, 
                q: pagination.query,
                state_id: stateId
            });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getCityById(id : string) : Promise<ICityResponse> {
    return new Promise<ICityResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_LOCATIONS}/cities/${id}`).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createCity(data : any) : Promise<ICityResponse> {
    return new Promise<ICityResponse>(async (resolve, reject) => {
        try {
            await api.post(`${ENDPOINT_LOCATIONS}/cities`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.city_created');
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

export async function updateCityById(id : string, data : any) : Promise<ICity> {
    return new Promise<ICity>(async (resolve, reject) => {
        try {
            await api.put(`${ENDPOINT_LOCATIONS}/cities/${id}`, data).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.city_updated');
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

export async function deleteCityById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            await api.delete(`${ENDPOINT_LOCATIONS}/cities/${id}`).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.city_deleted');
                resolve(response.data);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.form.delete_city');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
                reject(null);
            });  
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}
