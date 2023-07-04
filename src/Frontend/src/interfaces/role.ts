export interface IRole {
    id: string;
    display_name: object;
}

export interface IRolesResponse {
    items: Array<IRole>;
    pages: number;
    current_page: number;
    total: number;
}

export interface IRoleResponse {

}