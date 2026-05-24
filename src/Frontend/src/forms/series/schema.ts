import * as z from "zod";

export const SchemaSeries = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    code: z.string().min(1, { message: "toast.errors.form.required_field" }),
});

export const SchemaSeriesDefaultValues = {
    name: '',
    code: '',
};
