import axios, { AxiosResponse, AxiosError, InternalAxiosRequestConfig } from "axios";
// import Router from "next/router";
import { redirect } from 'next/navigation';
import Alert from "@/classes/Alert";
import { refreshToken } from "@/services/auth";
import { auth } from "@/libs/firebase/firebase";
import { IAuthSigninResponse } from "@/interfaces/auth";
import { getErrors } from "@/utils";
import { ALERT_ERROR } from "@/constants/alerts";
import { ENDPOINT_AUTH_REFRESH } from "@/constants/endpoints";
import { Auth } from "firebase/auth";
import { IErrorResponse } from "@/interfaces/error";
import { getCookie, setCookie } from "@/utils/auth";
import Router from "next/router";

const abortController = new AbortController();

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    headers: {
        "Access-Control-Allow-Origin": "*",
    },
    signal: abortController.signal,
});

const remakeRequest = async (config: InternalAxiosRequestConfig): Promise<AxiosResponse | null> => {
    const { method, url, data } = config;

    if (!method || !url) return null;

    try {
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
    } catch (error) {
        console.error(error);
        throw error; // Re-throw the error to be caught by the calling code
    }
};

api.interceptors.request.use(
    async (request: InternalAxiosRequestConfig) => {
        if (typeof window !== "undefined") {
            const cookiedToken = getCookie('token');
            const cookiedRefreshToken = getCookie('refresh_token');
            const token = request.url?.includes(ENDPOINT_AUTH_REFRESH) ? cookiedRefreshToken : cookiedToken;
            if (token) request.headers['Authorization'] = `Bearer ${token}`;
        }
        return request;
    },
    (error: AxiosError) => {
        console.error(error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response: AxiosResponse) => {
        // Any status code that lies within the range of 2xx causes this function to trigger
        // Do something with response data
        return response;
    },
    async (error: AxiosError) => {
        // Any status codes that fall outside the range of 2xx cause this function to trigger
        // Do something with response error

        if (!error.response || !error.response.data) return Promise.reject(error);

        const { data, config } = error.response;
        const status = error.response?.status || 500;

        if ((data as IErrorResponse).detail) {
            if (process.env.NODE_ENV === 'development') getErrors((data as IErrorResponse).detail);
            return Promise.reject(error);
        }

        if (status === 500) return Promise.reject(error);

        if (status === 400) {
            const { code, message } = data as IErrorResponse;
            if (process.env.NODE_ENV === 'development') getErrors([data]);
            return Promise.reject(error);
        }

        if (status === 401) {
            if (config.url?.includes(ENDPOINT_AUTH_REFRESH)) {
                console.warn('[EXPIRED TOKEN]: Redirecting...');
                window.location.replace('/');
                return Promise.reject(error);
            }

            const response: IAuthSigninResponse | null = await refreshToken(auth as Auth);
            if (!response) {
                new Alert().alert(ALERT_ERROR, 'error_api');
                return Promise.reject(error);
            }

            let email = "";
            const cookiedUser: string | null = getCookie('user');
            if (cookiedUser) email = JSON.parse(cookiedUser).email;

            const { access_token, refresh_token, id, scopes, user_name, user_id } = response;
            const user = { uid: id, scopes, user_name, email: email, user_id };

            setCookie('user', JSON.stringify(user));
            setCookie('token', access_token);
            setCookie('refresh_token', refresh_token);

            const data = await remakeRequest(config);
            if (!data) Promise.reject();

            return Promise.resolve();
        }

        if (status === 404) {
            const { code, message } = data as IErrorResponse;
            getErrors([data]);
            if (config.url?.includes(ENDPOINT_AUTH_REFRESH)) {
                //Router.push('/');
                return Promise.reject();
            }
            return Promise.resolve();
        }

        return Promise.reject(error);
    }
);

export { api, abortController };