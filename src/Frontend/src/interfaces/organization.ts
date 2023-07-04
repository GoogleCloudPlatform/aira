export interface IOrganization {
    id: string;
    name: string;
    city: string;
    state: string;
    created_at: Date;
    updated_at: Date;
}

export interface IOrganizationsResponse {
    items: Array<IOrganization>;
    pages: number;
    current_page: number;
    total: number;
}

export interface IOrganizationResponse {
    name: string;
    city: string;
    state: string;  
}