import { ColumnDef } from "@tanstack/react-table";
import { IAction } from "./action";
import { IIcon } from "./icon";
import { IUsersResponse } from "./user";

export type TTableHeader = {
    id: string;
    accessorKey: string
    header: string   
}

export interface ActionTableProps {
    columns: ColumnDef<TTableHeader>[],
    data: IUsersResponse | any,
    pagination: boolean
  }

export interface IActionTableInfoData {
    create: IActionTableInfoObject;
    edit: IActionTableInfoObject;
    delete: IActionTableInfoObject;
    _import: IActionTableInfoObject;
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
