import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { isEmpty } from "lodash";
import { getAllOrganizations } from "@/services/organization";
import { IOrganization } from "@/interfaces/organization";
import { TFormEditProps } from "@/interfaces/component";
import { SchemaEditGroupDefaultValues } from "./schema";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_GRADE_OPTIONS, ENUM_SHIFTS } from "@/constants/enums";
import { CATEGORY_GROUPS, CATEGORY_ORGANIZATIONS } from "@/constants";
import { updateGroupById } from "@/services/group";
import SkeletonSheet from "@/components/skeletons/SkeletonSheet";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";


const FormEditGroup : React.FC<TFormEditProps> = ({ formData, setOpen }) => {
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const queryClient = useQueryClient();
    const { data: organizationsOptions, isLoading: isLoadingOrganizations } = useQuery({ 
        queryKey: [CATEGORY_ORGANIZATIONS], 
        queryFn: () => getAllOrganizations(),
        retryOnMount: false, retry: false,
    });

    const { data, isLoading, isFetching } = useQuery<z.infer<typeof formData.schema>>({ queryKey: ['group'], queryFn: formData.defaultValues });

    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: data || SchemaEditGroupDefaultValues
    });

    useEffect(() => {
        if (data && !isEmpty(data)) {
            const newData = Object.assign({}, { ...data, organization_id: data.organization.id });
            form.reset(newData);
        }
    }, [data, form]);

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await updateGroupById(data.id, values);
            toast.success(t('toast.success.form.group_updated'))
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.edit_group'))
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: [CATEGORY_GROUPS] });
    }
    

    if (isLoading || isLoadingOrganizations || isFetching) return <SkeletonSheet />;

    if (!data || !organizationsOptions || isEmpty(data) || isEmpty(organizationsOptions)) return null;

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.group.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.group.edit.${field.name}`)}
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
                            <FormLabel>{t(`form.group.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.group.edit.${field.name}`)}
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

        if (fieldName === 'grade') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.group.edit.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                value={field.value || data.grade}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`form.group.edit.${field.name}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {ENUM_GRADE_OPTIONS.map((option) => (
                                        <SelectItem key={option.id} value={option.value}>
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

        if (fieldName === 'shift') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.group.edit.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                value={field.value || data.shift}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.group.edit.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {ENUM_SHIFTS.map((option) => (
                                        <SelectItem key={option.id} value={option.value}>
                                            {t(`form.group.edit.${option.name}`)}
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

        if (fieldName === 'organization_id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`${field.name === 'organization_id' ? 'form.group.edit.organization' : 'form.group.edit.'+field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                value={field.value || data.organization.id}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`${field.name === 'organization_id' ? 'form.group.edit.organization' : 'form.group.edit.'+field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {organizationsOptions.items.map((option: IOrganization) => (
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

        return (
            <></>
        )
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                    <div className="grid space-y-2">
                        {Object.keys(SchemaEditGroupDefaultValues).map((fieldName) => {
                            return (
                                <fieldset key={fieldName} className="field-item w-full">
                                    {renderField(fieldName)}
                                </fieldset>
                            );
                        })}
                    </div>
                    <div className="pt-5 w-full">
                        <Button type="submit" variant={"secondary"} disabled={loading} className="!w-full">
                            { !loading ?  t('form.group.edit.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormEditGroup;