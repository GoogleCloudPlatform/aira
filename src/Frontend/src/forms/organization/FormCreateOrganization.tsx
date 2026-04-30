import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TFormCreateProps } from "@/interfaces/component";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createOrganization } from "@/services/organization";
import { useQueryClient, useQuery } from "@tanstack/react-query";
import { CATEGORY_ORGANIZATIONS } from "@/constants";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";
import { useState, useEffect } from "react";
import { getCountries, getAllStates, getCities } from "@/services/location";

const FormCreateOrganization : React.FC<TFormCreateProps> = ({ formData, setOpen }) => {
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const queryClient = useQueryClient();
    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const [selectedCountry, setSelectedCountry] = useState<string>('');
    const [selectedState, setSelectedState] = useState<string>('');

    const { data: countriesData } = useQuery({
        queryKey: ['countries', 1],
        queryFn: getCountries,
    });

    const { data: statesData } = useQuery({
        queryKey: ['states', selectedCountry],
        queryFn: () => getAllStates(selectedCountry),
        enabled: !!selectedCountry
    });

    const { data: citiesData } = useQuery({
        queryKey: ['cities', selectedState],
        queryFn: () => getCities(selectedState),
        enabled: !!selectedState
    });

    useEffect(() => {
        if (countriesData?.items) {
            const defaultCountry = countriesData.items.find(c => c.is_default);
            if (defaultCountry && !selectedCountry) {
                setSelectedCountry(defaultCountry.id);
                form.setValue('country_id', defaultCountry.id);
            }
        }
    }, [countriesData, selectedCountry, form]);

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await createOrganization(values);
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.create_organization'))
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: [CATEGORY_ORGANIZATIONS] });
    }

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.create.${field.name}`)}
                                    type={"text"}
                                    disabled={true}
                                    value={field.value}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'name') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.create.${field.name}`)}
                                    type={"text"}
                                    disabled={field.disabled}
                                    value={field.value}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'country_id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={(value) => {
                                    field.onChange(value);
                                    setSelectedCountry(value);
                                    setSelectedState('');
                                    form.setValue('state_id', '');
                                    form.setValue('city_id', '');
                                }}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.create.${field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {countriesData?.items.map((option) => (
                                        <SelectItem key={option.id} value={option.id}>
                                            {option.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'state_id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={(value) => {
                                    field.onChange(value);
                                    setSelectedState(value);
                                    form.setValue('city_id', '');
                                }}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled || !selectedCountry}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.create.${field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {statesData?.map((option: any) => (
                                        <SelectItem key={option.id} value={option.id}>
                                            {option.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'city_id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled || !selectedState}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.create.${field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {citiesData?.items.map((option) => (
                                        <SelectItem key={option.id} value={option.id}>
                                            {option.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (['name', 'region'].includes(fieldName)) {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.create.${field.name}`)}
                                    type={"text"}
                                    disabled={field.disabled}
                                    value={field.value}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        return (
            <></>
        )
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                    <div className="grid space-y-2">
                        {Object.keys(formData.defaultValues).map((fieldName) => {
                            return (
                                <fieldset key={fieldName} className="field-item w-full">
                                    {renderField(fieldName)}
                                </fieldset>
                            );
                        })}
                    </div>
                    <div className="pt-5 w-full">
                        <Button type="submit" variant={"secondary"} disabled={loading} className="!w-full">
                            { !loading ?  t('form.organization.create.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormCreateOrganization;