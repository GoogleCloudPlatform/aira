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
    city: string;
    county: string;
    created_at: any;
    customer_id: string;
    id: string;
    name: string;
    region: string;
    state: string;  
    updated_at: any;
}

export interface IOrganizationsUtilsResponse {
    state: Array<string>;
    county: Array<string>;
    region: Array<string>;
}

export interface IOrganizationExportResponse {
    url: string;
}

export interface IOrganizationsImportResponse {

}