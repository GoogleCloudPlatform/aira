import { z } from "zod";

export const SchemaCreateCountry = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    code: z.string().min(1, { message: "toast.errors.form.required_field" }),
    is_default: z.boolean().default(false),
});

export const SchemaEditCountry = SchemaCreateCountry.extend({
    id: z.string(),
});

export const SchemaCreateCountryDefaultValues = {
    name: '',
    code: '',
    is_default: false,
};

export const SchemaCreateState = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    code: z.string().min(1, { message: "toast.errors.form.required_field" }),
    country_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
});

export const SchemaEditState = SchemaCreateState.extend({
    id: z.string(),
});

export const SchemaCreateStateDefaultValues = {
    name: '',
    code: '',
    country_id: '',
};

export const SchemaCreateCity = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    state_id: z.string().min(1, { message: "toast.errors.form.required_field" }),
});

export const SchemaEditCity = SchemaCreateCity.extend({
    id: z.string(),
});

export const SchemaCreateCityDefaultValues = {
    name: '',
    state_id: '',
};
