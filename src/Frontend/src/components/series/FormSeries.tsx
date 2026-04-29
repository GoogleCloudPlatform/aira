'use client';

import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import { createSeries, updateSeries } from "@/services/series";
import { SchemaSeries, SchemaSeriesDefaultValues } from "@/forms/series/schema";
import { MODE_CREATE, MODE_EDIT } from "@/constants";
import { useEffect } from "react";

interface FormSeriesProps {
    mode: string;
    formData: {
        defaultValues: any;
        category: string;
        id?: string;
    };
    setOpen: (open: boolean) => void;
}

const FormSeries: React.FC<FormSeriesProps> = ({ mode, formData, setOpen }) => {
    const t = useTranslations();
    const queryClient = useQueryClient();

    const form = useForm<z.infer<typeof SchemaSeries>>({
        resolver: zodResolver(SchemaSeries),
        defaultValues: SchemaSeriesDefaultValues,
    });

    useEffect(() => {
        if (mode === MODE_EDIT && formData.defaultValues) {
            if (typeof formData.defaultValues === 'function') {
                formData.defaultValues().then((data: any) => {
                    form.reset(data);
                });
            } else {
                form.reset(formData.defaultValues);
            }
        }
    }, [mode, formData, form]);

    const onSubmit = async (values: z.infer<typeof SchemaSeries>) => {
        try {
            if (mode === MODE_CREATE) {
                await createSeries(values);
                toast.success(t("toast.success.form.series_created"));
            } else if (mode === MODE_EDIT && formData.id) {
                await updateSeries(formData.id, values);
                toast.success(t("toast.success.form.series_updated"));
            }
            queryClient.invalidateQueries({ queryKey: [formData.category] });
            setOpen(false);
        } catch (error) {
            console.error(error);
            toast.error(t("toast.errors.form.action_failed"));
        }
    };

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>{t("table.headers.name")}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t("table.headers.name")} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="code"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>{t("table.headers.code")}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t("table.headers.code")} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                        {t("common.cancel")}
                    </Button>
                    <Button type="submit">
                        {mode === MODE_CREATE ? t("common.create") : t("common.save")}
                    </Button>
                </div>
            </form>
        </Form>
    );
};

export default FormSeries;
