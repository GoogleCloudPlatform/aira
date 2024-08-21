import { MAX_FILE_SIZE } from "@/constants";
import { ENUM_GROUPS_IMPORT } from "@/constants/enums";
import { isEmpty } from "lodash";
import { z } from "zod";

export const SchemaCreateGroup = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    grade: z.string().min(2, { message: "toast.errors.form.required_field" }),
    shift: z.string().min(1, { message: "toast.errors.form.required_field" }),
    organization_id: z.string().min(1, { message: "toast.errors.form.required_field" })
});

export const SchemaEditGroup = z.object({
    id: z.string().min(1, { message: "toast.errors.form.required_field" }),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    grade: z.string().min(2, { message: "toast.errors.form.required_field" }),
    shift: z.string().min(1, { message: "toast.errors.form.required_field" }),
    organization_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
}).pick({ name: true, grade: true, shift: true, organization_id: true });

export const SchemaImportGroup = z.object({
    file:typeof window === 'undefined' ? z.any() : z.instanceof(FileList).optional(),
    keys: z.array(z.object({
        type: z.string().refine(value => ENUM_GROUPS_IMPORT.some(option => option.value === value), {
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

export const SchemaCreateGroupDefaultValues : z.infer<typeof SchemaCreateGroup> = {
    name: '',
    grade: '',
    shift: '',
    organization_id: ''
}

export const SchemaEditGroupDefaultValues : z.infer<typeof SchemaEditGroup> & { id: string } = {
    id: '',
    name: '',
    grade: '',
    shift: '',
    organization_id: ''
}

export const SchemaImportGroupDefaultValues : z.infer<typeof SchemaImportGroup> = {
    file: undefined,
    keys: ENUM_GROUPS_IMPORT.map(item => ({
        type: item.value,
        data: ''
    }))
}