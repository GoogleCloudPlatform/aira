'use client';

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createState, updateStateById, getCountries } from "@/services/location";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";
import { MODE_CREATE, MODE_EDIT } from "@/constants";
import { useEffect } from "react";

interface FormStateProps {
    mode: typeof MODE_CREATE | typeof MODE_EDIT;
    formData: any;
    setOpen: (open: boolean) => void;
}

const FormState: React.FC<FormStateProps> = ({ mode, formData, setOpen }) => {
    const { loading, setLoading } = useLoading();
    const t = useTranslations();
    const queryClient = useQueryClient();

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const { data: countriesData } = useQuery({
        queryKey: ['countries', 1],
        queryFn: getCountries,
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
                await createState(values);
            } else if (mode === MODE_EDIT) {
                await updateStateById(formData.id, values);
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
                    name="country_id"
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.state.${mode}.country`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.state.${mode}.select_country`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {countriesData?.items.map((country) => (
                                        <SelectItem key={country.id} value={country.id}>
                                            {country.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.state.${mode}.name`)}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t(`form.state.${mode}.name`)} />
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
                            <FormLabel>{t(`form.state.${mode}.code`)}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t(`form.state.${mode}.code`)} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <div className="pt-5 w-full">
                    <Button type="submit" variant="secondary" disabled={loading} className="!w-full">
                        {!loading ? t(`form.state.${mode}.confirm`) : <Loading style="horizontal" text={true} size={16} />}
                    </Button>
                </div>
            </form>
        </Form>
    );
};

export default FormState;
