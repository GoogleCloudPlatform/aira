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
import { createShift, updateShift } from "@/services/shift";
import { SchemaShift, SchemaShiftDefaultValues } from "@/forms/shift/schema";
import { MODE_CREATE, MODE_EDIT } from "@/constants";
import { useEffect } from "react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface FormShiftProps {
    mode: string;
    formData: {
        defaultValues: any;
        category: string;
        id?: string;
    };
    setOpen: (open: boolean) => void;
}

const FormShift: React.FC<FormShiftProps> = ({ mode, formData, setOpen }) => {
    const t = useTranslations();
    const queryClient = useQueryClient();

    const form = useForm<z.infer<typeof SchemaShift>>({
        resolver: zodResolver(SchemaShift),
        defaultValues: SchemaShiftDefaultValues,
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

    const onSubmit = async (values: z.infer<typeof SchemaShift>) => {
        try {
            if (mode === MODE_CREATE) {
                await createShift(values);
                // Toast is handled in service layer!
            } else if (mode === MODE_EDIT && formData.id) {
                await updateShift(formData.id, values);
                // Toast is handled in service layer!
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
                    render={({ field }) => {
                        const shiftOptions = [
                            { value: "morning", label: t("table.shifts.morning") },
                            { value: "afternoon", label: t("table.shifts.afternoon") },
                            { value: "evening", label: t("table.shifts.evening") },
                            { value: "allday", label: t("table.shifts.allday") },
                        ];

                        return (
                            <FormItem>
                                <FormLabel>{t("table.headers.code")}</FormLabel>
                                <Select
                                    onValueChange={(val) => {
                                        field.onChange(val);
                                        const opt = shiftOptions.find(o => o.value === val);
                                        if (opt) {
                                            form.setValue("name", opt.label);
                                        }
                                    }}
                                    value={field.value}
                                >
                                    <FormControl>
                                        <SelectTrigger>
                                            <SelectValue placeholder={t("table.headers.code")} />
                                        </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        {shiftOptions.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                        );
                    }}
                />
                <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                        {t(`form.shift.${mode}.cancel`)}
                    </Button>
                    <Button type="submit">
                        {t(`form.shift.${mode}.confirm`)}
                    </Button>
                </div>
            </form>
        </Form>
    );
};

export default FormShift;
