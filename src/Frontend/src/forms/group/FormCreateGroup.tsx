import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getAllOrganizations } from "@/services/organization";
import { IOrganization } from "@/interfaces/organization";
import { TFormCreateProps } from "@/interfaces/component";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_GRADE_OPTIONS, ENUM_SHIFTS } from "@/constants/enums";
import { CATEGORY_GROUPS } from "@/constants";
import { createGroup } from "@/services/group";
import { isEmpty } from "lodash";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";

const FormCreateGroup : React.FC<TFormCreateProps> = ({ formData, setOpen }) => {
    const { loading, setLoading } = useLoading()
    
    const t = useTranslations("");
    const queryClient = useQueryClient();
    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const { data: organizations, isLoading } = useQuery({ 
        queryKey: ['organization'], 
        queryFn: () => getAllOrganizations(),
        retryOnMount: false, retry: false,
    });

    if (isLoading) return <>Loading...</>;
    if (!organizations || isEmpty(organizations)) return null;

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await createGroup(values);
            toast.success(t('toast.success.form.group_created'))
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.create_group'))
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: [CATEGORY_GROUPS] });
    }

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.group.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.group.create.${field.name}`)}
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
                            <FormLabel>{t(`form.group.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.group.create.${field.name}`)}
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

        if (['grade', 'shift', 'organization_id'].includes(fieldName)) {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`${field.name === 'organization_id' ? 'form.group.create.organization' : 'form.group.create.'+field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`${field.name === 'organization_id' ? 'form.group.create.organization' : 'form.group.create.'+field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                {fieldName === 'grade' && (
                                    <SelectContent>
                                        {ENUM_GRADE_OPTIONS.map((option) => (
                                            <SelectItem key={option.id} value={option.value}>
                                                {option.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                )}
                                {fieldName === 'shift' && (
                                    <SelectContent>
                                        {ENUM_SHIFTS.map((option) => (
                                            <SelectItem key={option.id} value={option.value}>
                                                {t(`form.group.create.${option.name}`)}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                )}
                                {fieldName === 'organization_id' && (
                                    <SelectContent>
                                        {!isEmpty(organizations.items) && organizations.items.map((option: IOrganization) => (
                                            <SelectItem key={option.id} value={option.id}>
                                                {option.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                )}
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
                            { !loading ?  t('form.group.create.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormCreateGroup;