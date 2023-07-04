export interface IInput {
    name: string;
    value: string | Array<string> | Array<any> | any;
    type: string;
    placeholder: string;
    label: string;
    required: boolean;
    options?: Array<IOption | any> | any;
    defaultOptions?: Array<IOption | any> | any; 
    multiple?: boolean;
    fields?: Array<IInput | any>;
    classes?: string; 
    disabled?: boolean;
    showLabel: boolean;
    render: boolean;
    dependencies?: Array<IDependence>;
    onChange?: (event : any) => void;
}

export interface IDependence {
    key: string;
    condition_values?: Array<string>;
    condition_multiple?: Array<string>;
    dynamic: boolean;
}

export interface IOption {
    name: string;
    id?: string;
    value?: string;
}