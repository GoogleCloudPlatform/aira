export interface IButton {
    name: string;
    action: () => void;
    icon?: string;
    size?: number;
    disabled?: boolean;
    classes?: string;
    loading?: boolean;
}