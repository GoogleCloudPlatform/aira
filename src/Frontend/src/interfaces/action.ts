import { IIcon } from "./icon";

export interface IAction extends IIcon {
    name: string;
    action(...args: any): void;
    scopes: Array<string>;
    text?: string;
    disabled: (item: any) => boolean;
    render: boolean;
}