import { IGroup } from "./group";
import { IOrganization } from "./organization";

export interface IUser {

}

export interface IUsersResponse {
    items: Array<IUser>;
    pages: number;
    current_page: number;
    total: number;
}

export interface IUserResponse {

}

export interface IProfileResponse {
    groups: Array<IGroup>;
    organizations: Array<IOrganization>;
}