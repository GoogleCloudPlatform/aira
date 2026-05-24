'use client';

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createCountry, updateCountryById } from "@/services/location";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";
import { MODE_CREATE, MODE_EDIT } from "@/constants";
import { useEffect } from "react";

interface FormCountryProps {
    mode: typeof MODE_CREATE | typeof MODE_EDIT;
    formData: any;
    setOpen: (open: boolean) => void;
}

const FormCountry: React.FC<FormCountryProps> = ({ mode, formData, setOpen }) => {
    const { loading, setLoading } = useLoading();
    const t = useTranslations();
    const queryClient = useQueryClient();

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    useEffect(() => {
        if (mode === MODE_EDIT && typeof formData.defaultValues === 'function') {
            formData.defaultValues().then((data: any) => {
                form.reset(data);
            });
        }
    }, [mode, formData, form]);

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true);
        try {
            if (mode === MODE_CREATE) {
                await createCountry(values);
            } else if (mode === MODE_EDIT) {
                await updateCountryById(formData.id, values);
            }
            setOpen(false);
        } catch (error) {
            toast.error(t('toast.errors.form.action_failed'));
        } finally {
            setLoading(false);
        }
        queryClient.invalidateQueries({ queryKey: [formData.category] });
    };

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.country.${mode}.name`)}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t(`form.country.${mode}.name`)} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="code"
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.country.${mode}.code`)}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t(`form.country.${mode}.code`)} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="is_default"
                    render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                            <FormControl>
                                <Checkbox
                                    checked={field.value}
                                    onCheckedChange={field.onChange}
                                />
                            </FormControl>
                            <div className="space-y-1 leading-none">
                                <FormLabel>{t(`form.country.${mode}.is_default`)}</FormLabel>
                            </div>
                        </FormItem>
                    )}
                />
                <div className="pt-5 w-full">
                    <Button type="submit" variant="secondary" disabled={loading} className="!w-full">
                        {!loading ? t(`form.country.${mode}.confirm`) : <Loading style="horizontal" text={true} size={16} />}
                    </Button>
                </div>
            </form>
        </Form>
    );
};

export default FormCountry;
