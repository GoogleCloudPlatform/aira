import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_IMPORT_TYPES, ENUM_USERS_IMPORT } from "@/constants/enums";
import { TFormImportProps } from "@/interfaces/component";
import { zodResolver } from "@hookform/resolvers/zod";
import { useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { isEmpty } from "lodash";
import { LucideTrash } from "lucide-react";
import { useTranslations } from "next-intl";
import { getProcessorImportSignedLink } from "@/services/processor";
import { fileListToBlob } from "@/utils";
import { uploadToGCS } from "@/services/gcs";
import { sendImportUsersDataGCS } from "@/services/user";
import { CATEGORY_USERS } from "@/constants";
import { useLoading } from "@/context/loading";
import { toast } from "react-toastify";
import Loading from "@/components/loading/Loading";

const FormImportUser : React.FC<TFormImportProps> = ({ formData, setOpen }) => {

    const t = useTranslations("form.user.import");
    const tToast = useTranslations("toast");
    const { loading, setLoading } = useLoading()
    const queryClient = useQueryClient();
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
        const type = ENUM_IMPORT_TYPES.user;
        const processor = await getProcessorImportSignedLink(type, mime_type).catch(() => {
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
            await sendImportUsersDataGCS(data)
            toast.success(tToast("success.form.import_user"));
        } catch (error) {
            toast.error(tToast("errors.form.import_user"));
        } finally {          
            setOpen(false);
            queryClient.invalidateQueries({ queryKey: [CATEGORY_USERS] });
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
            );
        }

        if (fieldName === 'keys') {
            return (
                <section className="space-y-2">
                    <FormLabel>{t("keys_relation")}</FormLabel>
                    {fields.map((field, index) => (
                        <fieldset key={field.id} className="flex w-full space-x-2">
                            <fieldset className="field-item flex-grow min-w-[160px]">
                                <FormField
                                    control={form.control}
                                    name={`keys.${index}.type`}
                                    render={({ field }) => {
                                        return (
                                            <FormItem className="space-y-2">
                                                {/* <FormLabel>{t(formData.defaultValues.keys[index].type)}</FormLabel> */}
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
                                                        {ENUM_USERS_IMPORT.map(option => (
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
                            <fieldset className="field-item">
                                <FormField
                                    control={form.control}
                                    name={`keys.${index}.data`}
                                    render={({ field }) => (
                                        <FormItem className="space-y-2">
                                            {/* <FormLabel>{t(formData.defaultValues.keys[index].)}</FormLabel> */}
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
                            onClick={() => append({ type: ENUM_USERS_IMPORT[0].value, data: '' })}
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

export default FormImportUser;