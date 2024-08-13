import Alert from "@/classes/Alert";
import { ALERT_ERROR } from "@/constants/alerts";
import { IError } from "@/interfaces/error";
//import { isEmpty } from "lodash";

export const getErrors = (errors : Array<IError>) : void => {
    try {
        Array.isArray(errors) && errors.map((error : IError) => {
            const text_error = error.type || error.code || "";
            new Alert().alert(ALERT_ERROR, text_error);
        });
    } catch (error) {
        console.error('[COULD NOT GET ERROR]:', error);
    }
}

export const getURL = (url: string, params: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    
    if (params) {
        Object.keys(params).forEach((param: string) => {
            const value = params[param];
            searchParams.append(param, value.toString());
        });
    }
    
    const queryString = searchParams.toString();

    if (queryString) {
        url += `?${queryString}`;
    }

    return url;
};

export const getFieldsFromData = (data : { [key: string]: any }) => {
    const output : { [key: string]: any } = {};
    
    Object.keys(data).map((key) => {
        const [form, field] = key.split("-");
        output[field] = data[key];
    });

    return output;
};

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

export const simulateRequest = async (seconds: number) : Promise<Object> => {
    return new Promise((resolve) => {
        setTimeout(() => {
            const resultObject: Object = {
                code: 200,
                message: "success"
            };
            resolve(resultObject);
        }, seconds * 1000); // Convert seconds to milliseconds
    });
}

export const fileListToBlob = (file: File) => {
    const blobs = [];
    blobs.push(file.slice(0, file.size, file.type));
    
    return new Blob(blobs);
}

export const getMimeTypeFromBase64 = (base64String: string) => {
    const match = base64String.match(/^data:([a-zA-Z0-9]+\/[a-zA-Z0-9-.+]+).*,/);
    if (match && match.length > 1) {
        return match[1];
    }
    return null;
}