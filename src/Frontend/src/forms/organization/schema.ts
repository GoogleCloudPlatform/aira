import { MAX_FILE_SIZE } from "@/constants";
import {  ENUM_ORGANIZATIONS_IMPORT, ENUM_STATE_OPTIONS } from "@/constants/enums";
import { isEmpty } from "lodash";
import { z } from "zod";

export const SchemaCreateOrganization = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    country_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    state_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    city_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    region: z.string().optional(),
});

export const SchemaEditOrganization = z.object({
    id: z.string(),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    country_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    state_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    city_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    region: z.string().optional(),
    created_at: z.date(),
    updated_at: z.date(),
}).pick({ name: true, country_id: true, state_id: true, city_id: true, region: true });

export const SchemaImportOrganization = z.object({
    file: typeof window === 'undefined' ? z.any() : z.instanceof(FileList).optional(),
    keys: z.array(z.object({
        type: z.string().refine(value => ENUM_ORGANIZATIONS_IMPORT.some(option => option.value === value), {
            message: "toast.errors.form.invalid_key",
        }),
        data: z.string()
    }))
}).superRefine(({ file }, ctx) => {
    if (isEmpty(file)) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_required",
            path: ["file"],
        })
    }

    if (file && !isEmpty(file) && !["text/csv"].includes(file[0].type)) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_csv",
            path: ["file"],
        })
    }

    if (file && !isEmpty(file) && file[0].size > MAX_FILE_SIZE) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.file_max_size_5",
            path: ["file"],
        })
    }
});

export const SchemaCreateOrganizationDefaultValues : z.infer<typeof SchemaCreateOrganization> = {
    name: '',
    country_id: '',
    state_id: '',
    city_id: '',
    region: ''
}

export const SchemaEditOrganizationDefaultValues : z.infer<typeof SchemaEditOrganization> & { id: string, created_at: Date, updated_at: Date } = {
    id: '',
    name: '',
    country_id: '',
    state_id: '',
    city_id: '',
    region: '',
    created_at: new Date(),
    updated_at: new Date()
}

export const SchemaImportOrganizationDefaultValues : z.infer<typeof SchemaImportOrganization> = {
    file: undefined,
    keys: ENUM_ORGANIZATIONS_IMPORT.map(item => ({
        type: item.value,
        data: ''
    }))
}