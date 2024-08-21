import { Dispatch, SetStateAction } from "react";
import { SchemaCreateUserDefaultValues, SchemaCreateUserForm } from "@/forms/user/schema";
import { IUserResponse } from "./user";
import { IOrganizationResponse } from "./organization";
import { SchemaCreateOrganizationDefaultValues, SchemaImportOrganization, SchemaImportOrganizationDefaultValues } from "@/forms/organization/schema";
import { CATEGORY_EXAMS, CATEGORY_GROUPS, CATEGORY_ORGANIZATIONS, CATEGORY_USERS, MODE_CREATE, MODE_DELETE, MODE_EDIT, MODE_IMPORT, MODE_VIEW } from "@/constants";
import { IExamResponse } from "./exam";
import { SchemaCreateExamDefaultValues } from "@/forms/exam/schema";
import { SchemaCreateGroupDefaultValues, SchemaImportGroup, SchemaImportGroupDefaultValues } from "@/forms/group/schema";
import { IGroupResponse } from "./group";

export type TCreateFormData = {
    schema: typeof SchemaCreateUserForm | any;
    defaultValues: typeof SchemaCreateUserDefaultValues | typeof SchemaCreateOrganizationDefaultValues | typeof SchemaCreateExamDefaultValues | typeof SchemaCreateGroupDefaultValues;  
    category: typeof CATEGORY_USERS | typeof CATEGORY_ORGANIZATIONS | typeof CATEGORY_EXAMS | typeof CATEGORY_GROUPS;
}

export type TEditFormData = {
    schema: typeof SchemaCreateUserForm | any;
    defaultValues: () => Promise<IUserResponse | IOrganizationResponse | IExamResponse | IGroupResponse>;
    category: typeof CATEGORY_USERS | typeof CATEGORY_ORGANIZATIONS | typeof CATEGORY_EXAMS | typeof CATEGORY_GROUPS;
}

export type TDeleteFormData = {
    category: typeof CATEGORY_USERS | typeof CATEGORY_ORGANIZATIONS | typeof CATEGORY_EXAMS | typeof CATEGORY_GROUPS;
    confirm: () => Promise<void>;
}


export type TImportFormData = {
    schema: typeof SchemaImportOrganization | typeof SchemaImportGroup;
    defaultValues: typeof SchemaImportOrganizationDefaultValues | typeof SchemaImportGroupDefaultValues ;  
    category: typeof CATEGORY_USERS | typeof CATEGORY_ORGANIZATIONS | typeof CATEGORY_GROUPS;
}

export type TFormProps = {
    formData: TCreateFormData | TEditFormData | TImportFormData, 
    setOpen: Dispatch<SetStateAction<boolean>>
}

export type TActionSheetCreate = {
    mode: typeof MODE_CREATE,
    formData: TCreateFormData
}

export type TActionSheetEdit = {
    mode: typeof MODE_EDIT,
    formData: TEditFormData
}

export type TActionSheetDelete = {
    mode: typeof MODE_DELETE,
    formData: TDeleteFormData
}

export type TActionSheetImport = {
    mode: typeof MODE_IMPORT,
    formData: TImportFormData
}

export type TActionSheetView = {
    mode: typeof MODE_VIEW,
    formData: TEditFormData
}

export type TActionSheetOptions = {
    title: string;
    subtitle: string;
} & (TActionSheetCreate | TActionSheetEdit | TActionSheetDelete | TActionSheetImport | TActionSheetView)

export type TActionSheet = {
    open: boolean;
    setOpen: Dispatch<SetStateAction<boolean>>;
    options: TActionSheetOptions;
}

export type TFormCreateProps = {
    formData: TCreateFormData, 
    setOpen: Dispatch<SetStateAction<boolean>>
}

export type TFormEditProps = {
    formData: TEditFormData, 
    setOpen: Dispatch<SetStateAction<boolean>>
}

export type TFormDeleteProps = {
    mode: typeof MODE_DELETE,
    title: string,
    formData: TDeleteFormData, 
    setOpen: Dispatch<SetStateAction<boolean>>
}

export type TFormImportProps = {
    formData: TImportFormData, 
    setOpen: Dispatch<SetStateAction<boolean>>
}

export interface IButton {
    name: string;
    action: () => void;
    icon?: string;
    size?: number;
    disabled?: boolean;
    classes?: string;
    loading?: boolean;
}

