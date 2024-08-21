import { z } from "zod";

// @TODO mapping errors globally - https://zod.dev/ERROR_HANDLING?id=customizing-errors-with-zoderrormap
export const SchemaSignIn = (t: any) => z.object({
    email: z.string().min(1, { message: "toast.errors.form.required_field" }).email("toast.errors.form.invalid_email"),
    password: z.string({
        invalid_type_error: 'toast.errors.form.invalid_password',
        required_error: "toast.errors.form.required_field",
        
    }).min(5, { message: 'toast.errors.form.min_password' }).max(50, { message: 'toast.errors.form.max_password' })
});

export const SchemaFormForgotPassword = (t: any) => z.object({
    password: z.string({
        invalid_type_error: t('toast.errors.form.invalid_password'),
        required_error: t("toast.errors.form.required_field"),
        
    }).min(5, { message: t('toast.errors.form.min_password', { min_size: 5 }) }).max(50, { message: t('toast.errors.form.max_password', { max_size: 50 }) }),
    confirm_password: z.string({
        invalid_type_error: t('toast.errors.form.invalid_password'),
        required_error: t("toast.errors.form.required_field"),
        
    }).min(5, { message: t('toast.errors.form.min_password', { min_size: 5 }) }).max(50, { message: t('toast.errors.form.max_password', { max_size: 50 }) })
}).superRefine(({ password, confirm_password }, ctx) => {
    if (confirm_password !== password) {
        ctx.addIssue({
            code: "custom",
            message: t("toast.errors.form.password_didnt_match"),
            path: ["confirm_password"],
        })
    }
});

export const FormSignInDefaultValues : z.infer<ReturnType<typeof SchemaSignIn>> = {
    email: '',
    password: ''
}

export const FormResetPasswordDefaultValues : z.infer<ReturnType<typeof SchemaFormForgotPassword>> = {
    password: '',
    confirm_password: ''
}