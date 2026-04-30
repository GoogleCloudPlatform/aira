import { useEffect, useState } from "react";
import { IOrganizationResponse } from "@/interfaces/organization";
import { SchemaEditOrganizationDefaultValues } from "./schema";
import { TFormEditProps } from "@/interfaces/component";
import { isEmpty } from "lodash";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import { CalendarIcon } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/libs/shadcn/utils";
import { Calendar } from "@/components/ui/calendar";
import { getFormattedDate } from "@/utils";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getCountries, getAllStates, getCities } from "@/services/location";
import { updateOrganizationById } from "@/services/organization";
import { CATEGORY_ORGANIZATIONS } from "@/constants";
import SkeletonSheet from "@/components/skeletons/SkeletonSheet";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";

const FormEditOrganization : React.FC<TFormEditProps> = ({ formData, setOpen }) => {
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const { locale } = useParams();
    const queryClient = useQueryClient();
    const { data, isLoading, isFetching } = useQuery<IOrganizationResponse | z.infer<typeof formData.schema>>({ queryKey: ['organization'], queryFn: formData.defaultValues });

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: data || SchemaEditOrganizationDefaultValues
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
        if (data && !isEmpty(data)) {
            setSelectedCountry(data.country_id || '');
            setSelectedState(data.state_id || '');
        }
    }, [data]);

    useEffect(() => {
        if (data && !isEmpty(data)) {
            const newData = Object.assign({}, data);
            form.reset(newData);
        }
    }, [data, form]);

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await updateOrganizationById(data.id, values);
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.edit_organization'))
        } finally {
            setLoading(false)
        }

        queryClient.invalidateQueries({ queryKey: [CATEGORY_ORGANIZATIONS] });
    }

    if (isLoading || isFetching) return <SkeletonSheet />;
    if (!data || isEmpty(data)) return null;

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.edit.${field.name}`)}
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
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.edit.${field.name}`)}
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
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={(value) => {
                                    field.onChange(value);
                                    setSelectedCountry(value);
                                    setSelectedState('');
                                    form.setValue('state_id', '');
                                    form.setValue('city_id', '');
                                }}
                                value={field.value || data.country_id}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.edit.${field.name}`)}`} />
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
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={(value) => {
                                    field.onChange(value);
                                    setSelectedState(value);
                                    form.setValue('city_id', '');
                                }}
                                value={field.value || data.state_id}
                                disabled={field.disabled || !selectedCountry}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.edit.${field.name}`)}`} />
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
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                value={field.value || data.city_id}
                                disabled={field.disabled || !selectedState}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.edit.${field.name}`)}`} />
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
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.organization.edit.${field.name}`)}
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

        if (fieldName === 'created_at' || fieldName === 'updated_at') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="flex flex-col">
                            <FormLabel>{t(`form.organization.edit.${field.name}`)}</FormLabel>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <FormControl>
                                        <Button
                                            variant={"outline"}
                                            disabled={true}
                                            className={cn(
                                                "pl-3 text-left font-normal dark:text-white",
                                                !field.value && "text-muted-foreground"
                                            )}
                                        >
                                            {field.value && (getFormattedDate(locale as string, new Date(field.value)))}
                                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                        </Button>
                                    </FormControl>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                    <Calendar
                                        mode="single"
                                        selected={field.value}
                                        onSelect={field.onChange}
                                        disabled={true}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>

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
                        {Object.keys(SchemaEditOrganizationDefaultValues).map((fieldName) => {
                            return (
                                <fieldset key={fieldName} className="field-item w-full">
                                    {renderField(fieldName)}
                                </fieldset>
                            );
                        })}
                    </div>
                    <div className="pt-5 w-full">
                        <Button type="submit" variant={"secondary"} disabled={loading} className="!w-full">
                            { !loading ?  t('form.organization.edit.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormEditOrganization;