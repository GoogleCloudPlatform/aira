export interface IMenuItem {
    name: string; 
    label: string;
    icon: string;
    render: boolean;
    route: string;
    items?: Array<IMenuItem>;
    highlight?: Array<string>;
    open?: boolean;
    order?: number;
    shouldRedirect?: boolean;
}