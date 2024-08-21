export type TOption = {
    label: string;
    value: string;
    id?: string; // comes from backend
}

export type TFormFields = {
    [key: string]: TInput
}

export type TRadio = {
    type: 'radio',
    options: Array<TOption>,
}

export type TSelect = {
    type: 'select',
    options: Array<TOption>,
    defaultOptions: Array<TOption>,
    multiple: boolean
}

type TCheckbox = {
    type: 'checkbox'
    options: Array<any>,
    multiple: boolean,
}

type TInputRule = {
    value: any;
    conditions: TInputConditions
}

type TInputConditions = {
    render: boolean,
    multiple: boolean
}

export type TDependsOfRules = {
    updateOwnOptions: boolean,
    depType: 'object' | 'array',
    rules: Array<TInputRule>
}

type TDependsOf = {
    [key: string]: TDependsOfRules
}

export type TInput = {
    //name: string;
    render: boolean;
    required: boolean,
    disabled: boolean,
} & (
    TSelect | 
    TCheckbox | 
    TRadio |
    { type: 'text' | 'email' | 'password' }
    //{ type: HTMLInputTypeAttribute }
)