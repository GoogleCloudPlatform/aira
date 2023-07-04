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
import { ALERT_SUCCESS } from "@/constants/alert";
import { ENDPOINT_PROFILE, ENDPOINT_USERS } from "@/constants/endpoint";
import { IProfileResponse, IUser, IUserResponse, IUsersResponse } from "@/interfaces/user";
import { api } from "@/pages/api/api";
import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getUsers() : Promise<IUsersResponse> {
    return new Promise<IUsersResponse>(async (resolve, reject) => {
        try {
            await api.get(ENDPOINT_USERS).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
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
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function createUser(data : any) : Promise<IUserResponse> {
    return new Promise<IUserResponse>(async (resolve, reject) => {
        try {
            const body = getBody(data);
            await api.post(ENDPOINT_USERS, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'user_created');
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function updateUserById(id : string, data : any) : Promise<IUser> {
    return new Promise<IUser>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${id}`;
            const body = getBody(data);
            await api.patch(url, body).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'user_edited');
                resolve(response.data);
            })
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function deleteUserById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_USERS}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'user_deleted');
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
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
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    })
}