import { IIcon } from "./icons";

export interface IAction extends IIcon {
    name: string;
    action(...args: any[]): void;
    render: boolean;
    scopes: Array<string>;
    text?: string;
}