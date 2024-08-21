export interface IError {
    loc?: Array<string>;
    msg?: string;
    type?: string;
    code?: string;
}

export interface IErrorResponse { // python backend response definition on error
    detail: IError[];
    code: string;
    message: string;
}
