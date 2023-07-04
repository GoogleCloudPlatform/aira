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
import { ENDPOINT_ROLES } from "@/constants/endpoint";
import { IRole, IRoleResponse, IRolesResponse } from "@/interfaces/role";
import { api } from "@/pages/api/api";
import { getURL } from "@/utils";
import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getRoles() : Promise<IRolesResponse> {
    return new Promise<IRolesResponse>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_ROLES, { page_size: 100 });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getRoleById(id : string) : Promise<IRoleResponse> {
    return new Promise<IRoleResponse>(async (resolve, reject) => {
        try {
            await api.get(`${ENDPOINT_ROLES}/${id}`).then(response => {
                const { data } = response;
                resolve(data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createRole(data : any) : Promise<IRoleResponse> {
    return new Promise<IRoleResponse>(async (resolve, reject) => {
        try {
            const body = getBody(data);
            await api.post(ENDPOINT_ROLES, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'role_created');
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

export async function updateRoleById(id : string, data : any) : Promise<IRole> {
    return new Promise<IRole>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ROLES}/${id}`;
            const body = getBody(data);
            await api.patch(url, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'role_edited');
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

export async function deleteRoleById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ROLES}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'role_deleted');
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