"use client"

import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { useLoading } from "@/context/loading";
import { isEmpty } from "lodash";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormResetPasswordDefaultValues, SchemaFormForgotPassword } from "@/forms/signin/schema";

import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormMessage,
} from "@/components/ui/form";
import { toast } from "react-toastify";
import { Button } from "@/components/ui/button"
import { PasswordInput } from "@/components/ui/extensions/password-input";
import Loading from "@/components/loading/Loading";
import { resetPassword } from "@/services/auth";

const FormResetPassword : React.FC = () => {
    const t = useTranslations();
    const tToast = useTranslations('toast');
    const { loading, setLoading } = useLoading();
    const params = useSearchParams();
    const router = useRouter()

    const formSchema = SchemaFormForgotPassword(t);
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: FormResetPasswordDefaultValues
    });

    const onSubmit = async (values: z.infer<typeof formSchema>) => {
        setLoading(true);
        const token = params.get("token");
        if (!token || isEmpty(token)) {
            console.error("[ERROR]: NO TOKEN PROVIDED");
            toast.error(tToast('errors.auth.error_missing_reset_token'))
            setLoading(false);
            return;
        }
        
        try {
            await resetPassword(token, values.password)
            form.clearErrors()
            toast.success(tToast('success.auth.success_reset_password'))
            router.push('/')
        } catch (error) {
            console.error(error)
            toast.error(tToast('errors.auth.failed_reset_password'))
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full">
                    <div className="flex flex-col gap-3">
                        <fieldset className="w-full">
                            <FormField
                                control={form.control}
                                name={"password"}
                                render={({ field }) => (
                                    <FormItem className="space-y-2">
                                        <FormControl>
                                            <PasswordInput
                                                id={field.name}
                                                value={field.value}
                                                onChange={field.onChange}
                                                autoComplete={field.name}
                                                disabled={field.disabled || loading}
                                                placeholder={t(`form.signin.${field.name}`)}
                                                className="border-border dark:border-darkBorder placeholder:capitalize text-black dark:text-white font-normal focus-visible:ring-border dark:focus-visible:ring-darkBorder" 
                                            />
                                        </FormControl>
                                        <FormMessage className="text-xs" />
                                    </FormItem>
                                )}
                            />
                        </fieldset>
                        <fieldset className="w-full">
                            <FormField
                                control={form.control}
                                name={"confirm_password"}
                                render={({ field }) => (
                                    <FormItem className="space-y-2">
                                        <FormControl>
                                            <PasswordInput
                                                id={field.name}
                                                value={field.value}
                                                onChange={field.onChange}
                                                autoComplete={field.name}
                                                disabled={field.disabled || loading}
                                                placeholder={t(`form.signin.${field.name}`)}
                                                className="border-border dark:border-darkBorder text-black dark:text-white font-normal focus-visible:ring-border dark:focus-visible:ring-darkBorder" 
                                            />
                                        </FormControl>
                                        <FormMessage className="text-xs" />
                                    </FormItem>
                                )}
                            />
                        </fieldset>
                    </div>
                
                    <Button type="submit" className="mt-6 w-full text-white bg-primary hover:bg-primary/90 dark:bg-darkPrimary dark:hover:bg-darkPrimary/90" disabled={loading}>
                        { !loading ?  t('form.signin.button_reset_password') : <Loading style="horizontal" text={true} size={16}/>}
                    </Button>
                </form>
            </Form>
        </>
    );
}

export default FormResetPassword;