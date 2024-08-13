import { z } from "zod";
import { useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { isEmpty } from "lodash";
import { useTranslations } from "next-intl";
import { sendImportGroupsDataGCS } from "@/services/group";
import { getProcessorImportSignedLink } from "@/services/processor";
import { uploadToGCS } from "@/services/gcs";
import { fileListToBlob } from "@/utils";
import { TFormImportProps } from "@/interfaces/component";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LucideTrash } from "lucide-react";
import { CATEGORY_GROUPS } from "@/constants";
import { ENUM_GROUPS_IMPORT, ENUM_IMPORT_TYPES } from "@/constants/enums";
import { useLoading } from "@/context/loading";
import { toast } from "react-toastify";
import Loading from "@/components/loading/Loading";

const FormImportGroup : React.FC<TFormImportProps> = ({ formData, setOpen }) => {
    
    const t = useTranslations("form.group.import");
    const tToast = useTranslations("toast");
    const queryClient = useQueryClient();
    const { loading, setLoading } = useLoading()
    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: formData.defaultValues
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: 'keys',
    })

    const fileRef = form.register("file");

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        const file = values.file ? values.file[0] : null;
        if (!file) return;
        
    
        const mime_type = file.type;
        const processor = await getProcessorImportSignedLink(ENUM_IMPORT_TYPES.group, mime_type).catch(() => {
            //toast.error(t("error_sending_import"))
            //setSettings("loading", false)
        });

        if (!processor) return;

        const { signed_url } = processor;
        const file_to_send = fileListToBlob(file);
        const uploadUrl = await uploadToGCS(signed_url, file_to_send, mime_type).catch(() => {
            //toast.error(t("error_sending_import"))
            //setSettings("loading", false)
        });

        if (!uploadUrl) return;

        const key_relation: { [key: string]: string } = {};
        values.keys.forEach((item) => {
            if (!isEmpty(item.data)) {
                key_relation[item.data] = item.type;
            }
        });

        const data = {
            url: uploadUrl,
            key_relation: key_relation
        }
        
        try {
            await sendImportGroupsDataGCS(data)
            toast.success(tToast("success.form.import_group"));
        } catch (error) {
            toast.error(tToast("errors.form.import_group"));
        } finally {          
            setOpen(false);
            queryClient.invalidateQueries({ queryKey: [CATEGORY_GROUPS] });
            setLoading(false)
        }
    }

    const renderField = (fieldName: string) => {
        if (fieldName === 'file') {
            return ( 
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(field.name)}</FormLabel>
                            <FormControl>
                                <Input
                                    id="file"
                                    type={"file"}
                                    {...fileRef}
                                />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'keys') {
            return (
                <section className="space-y-2">
                    <FormLabel>{t("keys_relation")}</FormLabel>
                    {fields.map((field, index) => (
                        <fieldset key={field.id} className="flex w-full space-x-2">
                            <fieldset className="field-item flex-grow w-full">
                                <FormField
                                    control={form.control}
                                    name={`keys.${index}.type`}
                                    render={({ field }) => {
                                        return (
                                            <FormItem className="space-y-2">
                                                <Select
                                                    onValueChange={field.onChange}
                                                    defaultValue={field.value}
                                                    value={field.value}
                                                    disabled={field.disabled}
                                                >
                                                    <FormControl>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder={field.name} />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        {ENUM_GROUPS_IMPORT.map(option => (
                                                            <SelectItem key={option.value} value={option.value}>
                                                                {t(option.label)}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                                <FormMessage />
                                            </FormItem>
                                        )    
                                    }}
                                />
                            </fieldset>
                            <fieldset className="field-item w-full">
                                <FormField
                                    control={form.control}
                                    name={`keys.${index}.data`}
                                    render={({ field }) => (
                                        <FormItem className="space-y-2">
                                            <FormControl>
                                                <Input
                                                    {...field}
                                                    placeholder={t("value")}
                                                    type={"text"}
                                                    disabled={field.disabled}
                                                    value={field.value}
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </fieldset>
                            <i className="flex flex-col-reverse flex-shrink">
                                <Button 
                                    size={"icon"} 
                                    variant="destructive"
                                    className={`p-2 w-9 h-9`} 
                                    onClick={() => remove(index)} 
                                    title={"remove"}
                                >
                                    <LucideTrash className="w-10 h-10" />
                                </Button>
                            </i>
                        </fieldset>
                    ))}

                    
                    <div className="block">
                        <Button 
                            type="button" 
                            className="w-full" 
                            onClick={() => append({ type: ENUM_GROUPS_IMPORT[0].value, data: '' })}
                        >
                            {t("add_key")}
                        </Button>
                    </div>
                </section>
            )
        }
    
        return null;
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                    <div className="grid space-y-2">
                        {Object.keys(formData.defaultValues).map((fieldName) => 
                            <fieldset key={fieldName} className="field-item w-full">
                                {renderField(fieldName)}
                            </fieldset>
                        )}
                    </div>
                    <div className="w-full">
                        <Button type="submit" variant={"secondary"} disabled={loading} className="!w-full">
                            { !loading ?  t('confirm') : <Loading style="horizontal" text={true} size={16}/>}
                        </Button>
                    </div>
                </form>
            </Form>
        </>
    )
}

export default FormImportGroup;