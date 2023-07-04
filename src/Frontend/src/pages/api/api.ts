import axios from "axios";
import Router from "next/router";
import Alert from "@/classes/Alert";
import { refreshToken } from "@/services/auth";
import { auth } from '@/libs/firebase';
import { IAuthSigninResponse } from "@/interfaces/auth";
import { isEmpty } from "lodash";
import { getErrors } from "@/utils";
import getConfig from "next/config";
import { ALERT_ERROR } from "@/constants/alert";
import { ENDPOINT_AUTH_REFRESH } from "@/constants/endpoint";
import { Auth } from "firebase/auth";

const { publicRuntimeConfig } = getConfig();

const abortController = new AbortController();

const api = axios.create({
    baseURL: publicRuntimeConfig.NEXT_PUBLIC_API_URL,
    headers: {
        "Access-Control-Allow-Origin": "*",
    },
    signal: abortController.signal
});


const remakeRequest = async (config : any) => {
    const { method, url, data } = config;

    switch (method.toUpperCase()) {
        case "GET":
            return api.get(url).then(response => response);
        case "PATCH":
            return api.patch(url, data).then(response => response);
        case "POST":
            return api.post(url, data).then(response => response);
        case "DELETE":
            return api.delete(url).then(response => response);
        default:
            return null;
    }
}

api.interceptors.request.use(
    async (request : any) => {
        if (typeof window !== "undefined") {
            const storageToken = localStorage.getItem('token');
            const refreshToken = localStorage.getItem('refresh_token');
            const token = request.url.includes(ENDPOINT_AUTH_REFRESH) ? refreshToken : storageToken;
            if (token) request.headers['Authorization'] = `Bearer ${token}`;
        }
        return request;
    }, 
    (error) => {
        console.error(error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response : any) => {
        // Any status code that lie within the range of 2xx cause this function to trigger
        // Do something with response data
        return response;
    }, 
    async (error) => {
        // Any status codes that falls outside the range of 2xx cause this function to trigger
        // Do something with response error
        
        if (!error.response || !error.response.data) return Promise.reject(error);

        const { data, config } = error.response;
        const status = error.response?.status || 500;

        if (data.detail) {
            getErrors(data.detail);
            return Promise.reject();
        }

        if (status === 500) return Promise.reject();

        if (status === 400) {
            const { code, message } = data;
            getErrors([data]);
            return Promise.reject();
        }

        if (status === 401) {
            if (config.url.includes(ENDPOINT_AUTH_REFRESH)) {
                Router.push('/');
                return Promise.reject();
            }

            const response : (IAuthSigninResponse | null) = await refreshToken(auth as Auth);
            if (!response) {
                new Alert().alert(ALERT_ERROR, 'error_api');
                return Promise.reject();
            }

            let email = "";
            const userStorage : (string | null) = localStorage.getItem('user');
            if (userStorage) email = JSON.parse(userStorage).email;

            const { access_token, refresh_token, id, scopes, user_name } = response;
            const user = { uid: id, scopes, user_name, email: email };

            await localStorage.setItem('user', JSON.stringify(user));
            await localStorage.setItem('token', access_token); 
            await localStorage.setItem('refresh_token', refresh_token); 

            return Promise.resolve();
        }

        if (status === 404) {
            const { code, message } = data;
            getErrors([data]);
            if (config.url.includes(ENDPOINT_AUTH_REFRESH)) {
                Router.push('/');
                return Promise.reject();
            }
            return Promise.resolve();
        }
        
        return Promise.reject(error);
    }
);

export { api, abortController };