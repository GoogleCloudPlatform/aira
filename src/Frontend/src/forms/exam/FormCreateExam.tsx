import { useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { z } from "zod";
import { ptBR, enUS, es } from "date-fns/locale";
import { TFormCreateProps } from "@/interfaces/component";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createExam } from "@/services/exam";
import { getFormattedDate } from "@/utils";
import { getSeries } from "@/services/series";

import QuestionPreview from "@/components/question-preview/QuestionsPreview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { CalendarIcon } from "lucide-react";
import { cn } from "@/libs/shadcn/utils";
import { IQuestion } from "@/interfaces/question";
import { isEmpty } from "lodash";
import { TimePicker } from "@/components/ui/time-picker";
import { toast } from "react-toastify";
import Loading from "@/components/loading/Loading";
import { useLoading } from "@/context/loading";
import FormQuestions from "./FormQuestions";
import { SchemaCreateExam, SchemaCreateExamDefaultValues } from "./schema";
import { useQuestions } from "@/context/questions";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_GRADE_OPTIONS } from "@/constants/enums";

const FormCreateExam : React.FC<TFormCreateProps> = ({ setOpen }) => {
    const [startDate, setStartDate] = useState<Date>(new Date());
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const { locale } = useParams();
    const queryClient = useQueryClient();

    const { data: seriesData } = useQuery({
        queryKey: ['series'],
        queryFn: () => getSeries(),
    });

    const { form, resetForm } = useQuestions()

    const { errors } = form.formState

    const { questions } = form.watch('questions')

    const onSubmit = async (values: z.infer<typeof SchemaCreateExam>) => {
        setLoading(true)
        try {
            await createExam(values);
            resetForm()
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.create_exam'))
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: ['exams'] });
    }

    const handleCancel = ()=>{
        setOpen(false)
        resetForm()
    }

    const handleSelectDay = (day: Date | undefined, onChange:any) => {
        if (day) {
            setStartDate(day)
        }
        onChange(day)
    }

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.exam.create.${field.name}`)}
                                    type={"text"}
                                    disabled={true}
                                    value={field.value}
                                />
                            </FormControl>
                            {errors[field.name] && (
                                <span className="text-red-500 text-sm">{t(errors[field.name]?.message && errors[field.name]?.message?.toString())}</span>
                            )}
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
                            <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.exam.create.${field.name}`)}
                                    type={"text"}
                                    disabled={field.disabled}
                                    value={field.value}
                                />
                            </FormControl>
                            {errors[field.name] && (
                                <span className="text-red-500 text-sm">{errors[field.name]?.message && t(errors[field.name]?.message?.toString())}</span>
                            )}
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'questions') {
            return (
                <FormQuestions />
            )
        }

        if (fieldName === 'grade') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                            <Select
                                onValueChange={field.onChange}
                                defaultValue={field.value}
                                value={field.value}
                                disabled={field.disabled}
                            >
                                <FormControl>
                                    <SelectTrigger>
                                        <SelectValue placeholder={t(`form.exam.create.${field.name}`)} />
                                    </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                    {seriesData?.items?.map((option: any, index: number) => (
                                        <SelectItem key={index} value={option.name}>
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

        if (['start_date', 'end_date'].includes(fieldName)) {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2 flex flex-col">
                            <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                            <Popover>
                                <FormControl>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant="outline"
                                            className={cn(
                                                "w-full justify-start text-left font-normal dark:text-white",
                                                !field.value && "text-muted-foreground"
                                            )}
                                        >
                                            <CalendarIcon className="mr-2 h-4 w-4" />
                                            {field.value && (getFormattedDate(locale as string, new Date(field.value)))}
                                        </Button>
                                    </PopoverTrigger>
                                </FormControl>
                                <PopoverContent className="w-auto p-0">
                                    <Calendar
                                        mode="single"
                                        selected={field.value instanceof Date ? field.value : new Date(field.value)}
                                        onSelect={fieldName === 'start_date' ? (day) => handleSelectDay(day, field.onChange) : field.onChange}
                                        initialFocus
                                        fromDate={fieldName === 'start_date' ? new Date() : startDate} 
                                        locale={locale === 'es-ES' ? es : locale === 'en-US' ? enUS : ptBR}
                                    />
                                    <div className="p-3 border-t border-border dark:border-darkBorder">
                                        <TimePicker
                                            setDate={field.onChange}
                                            date={field.value instanceof Date ? field.value : new Date(field.value)}
                                        />
                                    </div>
                                </PopoverContent>
                            </Popover>
                            {errors[field.name] && (
                                <span className="text-red-500 text-sm">{errors[field.name]?.message && t(errors[field.name]?.message?.toString())}</span>
                            )}
                        </FormItem>
                    )}
                />
            )
        }

        return null;
    }

    return (
        <>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                    <div className="grid space-y-2">
                        {Object.keys(SchemaCreateExamDefaultValues).map((fieldName) => {
                            return (
                                <fieldset key={fieldName} className="field-item w-full">
                                    {renderField(fieldName)}
                                </fieldset>
                            );
                        })}
                    </div>
                    <div className="flex w-full gap-4 items-center">
                        <div className="flex w-full gap-2 items-center">
                            <Button type="submit" variant={"secondary"} className="w-full" disabled={loading}>
                                { !loading ?  t('form.exam.create.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                            </Button>
                            {questions && questions.find((q: IQuestion)=> !isEmpty(q.data)) && (
                                <QuestionPreview questions={questions}/>   
                            )}
                        </div>
                    </div>

                    {!loading && (
                        <Button variant="destructive" type="button" onClick={handleCancel} className="w-full">
                            {t('form.exam.create.cancel')}
                        </Button>
                    )}
                </form>
            </Form>
        </>
    )
}

export default FormCreateExam;