import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_STATE_OPTIONS } from "@/constants/enums";
import { TFormCreateProps } from "@/interfaces/component";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createOrganization } from "@/services/organization";
import { useQueryClient } from "@tanstack/react-query";
import { CATEGORY_ORGANIZATIONS } from "@/constants";
import { useTranslations } from "next-intl";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import Loading from "@/components/loading/Loading";

const FormCreateOrganization : React.FC<TFormCreateProps> = ({ formData, setOpen }) => {
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const queryClient = useQueryClient();
    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await createOrganization(values);
            toast.success(t('toast.success.form.organization_created'))
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

        if (fieldName === 'state') {
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
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={`${t(`form.organization.create.${field.name}`)}`} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {ENUM_STATE_OPTIONS.map((option, index) => (
                                        <SelectItem key={index} value={option.value}>
                                            {option.label}
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

        if (['name', 'region', 'city', 'county'].includes(fieldName)) {
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