export interface IMenuItem {
    name: string; 
    label: string;
    icon: string;
    render: boolean;
    route: string;
    items?: Array<IMenuItem>;
    open?: boolean;
    order?: number;
}