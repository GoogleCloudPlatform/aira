import { IOrganization } from "./organization";

export interface IGroup {
    grade: string;
    shift: string;
    organization: IOrganization;
    created_at: Date;
    updated_at: Date;
    name: string;
}

export interface IGroupsResponse {
    items: Array<IGroup>;
    pages: number;
    current_page: number;
    total: number;
}

export interface IGroupResponse {

}