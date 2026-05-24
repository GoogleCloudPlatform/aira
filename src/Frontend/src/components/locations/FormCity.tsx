'use client';

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createCity, updateCityById, getCountries, getAllStates } from "@/services/location";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";
import { MODE_CREATE, MODE_EDIT } from "@/constants";
import { useEffect, useState } from "react";

interface FormCityProps {
    mode: typeof MODE_CREATE | typeof MODE_EDIT;
    formData: any;
    setOpen: (open: boolean) => void;
}

const FormCity: React.FC<FormCityProps> = ({ mode, formData, setOpen }) => {
    const { loading, setLoading } = useLoading();
    const t = useTranslations();
    const queryClient = useQueryClient();

    const [selectedCountry, setSelectedCountry] = useState<string>('');

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const { data: countriesData } = useQuery({
        queryKey: ['countries', 1],
        queryFn: getCountries,
    });

    const { data: statesData } = useQuery({
        queryKey: ['states', selectedCountry],
        queryFn: () => getAllStates(selectedCountry),
        enabled: !!selectedCountry,
        retry: false
    });

    useEffect(() => {
        if (mode === MODE_EDIT && typeof formData.defaultValues === 'function') {
            formData.defaultValues().then((data: any) => {
                form.reset(data);
                if (data.state && data.state.country_id) {
                    setSelectedCountry(data.state.country_id);
                }
            });
        }
    }, [mode, formData, form]);

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true);
        try {
            if (mode === MODE_CREATE) {
                await createCity(values);
            } else if (mode === MODE_EDIT) {
                await updateCityById(formData.id, values);
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
                <FormItem className="space-y-2">
                    <FormLabel>{t(`form.city.${mode}.country`)}</FormLabel>
                    <Select
                        onValueChange={setSelectedCountry}
                        value={selectedCountry}
                    >
                        <FormControl>
                            <SelectTrigger>
                                <SelectValue placeholder={t(`form.city.${mode}.select_country`)} />
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
                </FormItem>
                <FormField
                    control={form.control}
                    name="state_id"
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.city.${mode}.state`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={!selectedCountry}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.city.${mode}.select_state`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {statesData?.map((state: any) => (
                                        <SelectItem key={state.id} value={state.id}>
                                            {state.name}
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
                            <FormLabel>{t(`form.city.${mode}.name`)}</FormLabel>
                            <FormControl>
                                <Input {...field} placeholder={t(`form.city.${mode}.name`)} />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <div className="pt-5 w-full">
                    <Button type="submit" variant="secondary" disabled={loading} className="!w-full">
                        {!loading ? t(`form.city.${mode}.confirm`) : <Loading style="horizontal" text={true} size={16} />}
                    </Button>
                </div>
            </form>
        </Form>
    );
};

export default FormCity;
