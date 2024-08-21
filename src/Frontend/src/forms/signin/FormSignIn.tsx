"use client"

import { useAuth } from "@/context/auth";
import { useTranslations } from "next-intl";
import { FormSignInDefaultValues, SchemaSignIn } from "@/forms/signin/schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { forgotPassword } from "@/services/auth";
import { isEmpty } from "lodash";
import { useLoading } from "@/context/loading";
import { PasswordInput } from "@/components/ui/extensions/password-input";
import Loading from "@/components/loading/Loading";
import { toast } from "react-toastify";

const FormSignIn : React.FC = () => {
    const t = useTranslations('form.signin');
    const tToast = useTranslations('toast');
    const { signIn } = useAuth();
    const { loading, setLoading } = useLoading();
    
    const formSchema = SchemaSignIn(t);
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: FormSignInDefaultValues
    });

    const onSubmit = async (values: z.infer<typeof formSchema>) => {
        const { email, password } = values;
        await signIn(email, password);
    }

    const handleRecoverPassword = async () => {
        setLoading(true)
        const email = form.watch("email");
        if (!email || isEmpty(email)) return form.trigger("email");

        try {
            await forgotPassword(email)
            form.clearErrors()
            toast.success(tToast('success.auth.reset_password_email_sent'))
        } catch (error) {
            console.error(error)
            toast.error(tToast('errors.auth.reset_password_email_sent_error'))
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
                                name={"email"}
                                render={({ field }) => (
                                    <FormItem>
                                        <FormControl>
                                            <Input 
                                                {...field}
                                                placeholder={t(field.name)}
                                                className="border-border dark:border-darkBorder placeholder:capitalize text-black dark:text-white font-normal focus-visible:ring-border dark:focus-visible:ring-darkBorder" 
                                                disabled={field.disabled || loading}
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
                                                placeholder={t(field.name)}
                                                className="border-border dark:border-darkBorder placeholder:capitalize text-black dark:text-white font-normal focus-visible:ring-border dark:focus-visible:ring-darkBorder" 
                                            />
                                        </FormControl>
                                        <FormMessage className="text-xs" />
                                    </FormItem>
                                )}
                            />
                        </fieldset>
                    </div>

                    <div className="w-full text-end mb-3">
                        <button 
                            className="text-xs text-primary font-medium dark:text-white hover:underline"
                            onClick={handleRecoverPassword}
                            type="button"
                            disabled={loading}
                        >
                            {t('forgot_password')}?
                        </button>
                    </div>
                
                    <Button type="submit" className="w-full text-white bg-primary hover:bg-primary/90 dark:bg-darkPrimary dark:hover:bg-darkPrimary/90" disabled={loading}>
                        { !loading ?  t('button_sign_in') : <Loading style="horizontal" text={true} size={16}/>}
                    </Button>
                </form>
            </Form>
        </>
    );
}

export default FormSignIn;