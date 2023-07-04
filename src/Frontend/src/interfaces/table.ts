import { IAction } from "./actions";
import { IIcon } from "./icons";

export interface IActionTable {
    data: any;
    fields?: Array<string>;
    actions: Array<IAction>;
    pagination: boolean;
}

export interface IActionTableInfoData {
    create: IActionTableInfoObject;
    edit: IActionTableInfoObject;
    delete: IActionTableInfoObject;
}

export interface IActionTableInfoObject {
    title: string;
    message: string;
    icon: IIcon;
}

export interface IActionTablePagination {
    items: Array<any>;
    //current_page: number;
    pages: number;
    total: number;
}
