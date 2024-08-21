import Alert from "@/classes/Alert";
import { ALERT_ERROR, ALERT_SUCCESS } from "@/constants/alerts";
import { ENDPOINT_ROLES } from "@/constants/endpoints";
import { IRole, IRoleResponse, IRolesResponse } from "@/interfaces/roles";
import { api } from "@/api/api";
import { getURL } from "@/utils";
//import { getBody } from "@/utils/form";

const AlertInstance = new Alert();

export async function getAllRoles() : Promise<IRolesResponse> {
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

// export async function createRole(data : any) : Promise<IRoleResponse> {
//     return new Promise<IRoleResponse>(async (resolve, reject) => {
//         try {
//             const body = getBody(data);
//             await api.post(ENDPOINT_ROLES, body).then(response => {         
//                 AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.role_created');
//                 resolve(response.data);
//             }).catch((error: any) => {
//                 AlertInstance.alert(ALERT_ERROR, 'error_api');
//                 if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
//                 reject(null);
//             });  
//         } catch (e) {
//             if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
//             reject(null);
//         }
//     });
// }

// export async function updateRoleById(id : string, data : any) : Promise<IRole> {
//     return new Promise<IRole>(async (resolve, reject) => {
//         try {
//             const url = `${ENDPOINT_ROLES}/${id}`;
//             const body = getBody(data);
//             await api.patch(url, body).then(response => {         
//                 AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.role_updated');
//                 resolve(response.data);
//             }).catch((error: any) => {
//                 AlertInstance.alert(ALERT_ERROR, 'error_api');
//                 if (process.env.NODE_ENV === 'development') console.error('API ERROR: ' + error);
//                 reject(null);
//             });  
//         } catch (e) {
//             if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
//             reject(null);
//         }
//     });
// }

export async function deleteRoleById(id : string) : Promise<void> {
    return new Promise<void>(async (resolve, reject) => {
        try {
            const url = `${ENDPOINT_ROLES}/${id}`;
            await api.delete(url).then(response => {         
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.form.role_deleted');
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