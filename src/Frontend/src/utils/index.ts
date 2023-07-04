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
import { IError } from "@/interfaces/error";
import { isEmpty } from "lodash";
import { i18n } from "next-i18next";
import { toast } from "react-toastify";

export const getErrors = (errors : Array<IError>) : void => {
    errors.map((error : IError) => {
        const text_error = error.type || error.code || "";
        toast.error(i18n?.t(text_error, { ns: "toast" }));
    });
}

export const getURL = (url: string, params: any) : string => {
    if (!isEmpty(params)) {
        Object.keys(params).map((param : any, i: number) => {
            const value = params[param];
            if (i == 0) url += `?${param}=${value}`
            else url += `&${param}=${value}`;
        });
    }

    return url;
}

export const getFormattedDate = (locale: string, dateTime: Date) => {
    const options: any = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: 'numeric',
        minute: 'numeric'
    };
    const formattedDate = new Intl.DateTimeFormat(locale, options).format(dateTime);
    return formattedDate;
};
  
export const formatInputDate = (dateTime: string) => {
    const date = new Date(dateTime);
    
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    
    const formattedDate = `${year}-${month}-${day}T${hour}:${minute}`;
    return formattedDate;
};

export const getMimeTypeFromBase64 = (base64String: string) => {
    const match = base64String.match(/^data:([a-zA-Z0-9]+\/[a-zA-Z0-9-.+]+).*,/);
    if (match && match.length > 1) {
        return match[1];
    }
    return null;
}