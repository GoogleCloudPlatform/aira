export interface ICountry {
    id: string;
    name: string;
    code: string;
    is_default: boolean;
    created_at: string;
    updated_at: string;
}

export interface ICountryResponse extends ICountry {}

export interface ICountriesResponse {
    items: ICountry[];
    pages: number;
    current_page: number;
    total: number;
}

export interface IState {
    id: string;
    name: string;
    code: string;
    country_id: string;
    created_at: string;
    updated_at: string;
}

export interface IStateResponse extends IState {}

export interface IStatesResponse {
    items: IState[];
    pages: number;
    current_page: number;
    total: number;
}

export interface ICity {
    id: string;
    name: string;
    state_id: string;
    created_at: string;
    updated_at: string;
}

export interface ICityResponse extends ICity {}

export interface ICitiesResponse {
    items: ICity[];
    pages: number;
    current_page: number;
    total: number;
}
