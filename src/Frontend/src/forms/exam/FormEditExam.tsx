import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { enUS, es, ptBR } from "date-fns/locale";
import { TFormEditProps } from "@/interfaces/component";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import QuestionPreview from "@/components/question-preview/QuestionsPreview";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { CalendarIcon } from "lucide-react";
import { cn } from "@/libs/shadcn/utils";
import { getFormattedDate } from "@/utils";
import { useParams } from "next/navigation";
import { IExamResponse } from "@/interfaces/exam";
import { SchemaEditExamDefaultValues } from "./schema";
import { isEmpty } from "lodash";
import { updateExamById } from "@/services/exam";
import { IQuestion } from "@/interfaces/question";
import { getSeries } from "@/services/series";
import { TimePicker } from "@/components/ui/time-picker";
import SkeletonSheet from "@/components/skeletons/SkeletonSheet";
import Loading from "@/components/loading/Loading";
import { toast } from "react-toastify";
import { useLoading } from "@/context/loading";
import FormQuestions from "./FormQuestions";
import { useQuestions } from "@/context/questions";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ENUM_GRADE_OPTIONS } from "@/constants/enums";

type TViewProps = {
    preview?: boolean
}

interface FormEditExamProps extends TFormEditProps, TViewProps {}

const FormEditExam : React.FC<FormEditExamProps> = ({ formData, setOpen, preview = false }) => {
    const [startDate, setStartDate] = useState<Date>(new Date());
    const { loading, setLoading } = useLoading()
    
    const t = useTranslations();
    const { locale } = useParams();
    const queryClient = useQueryClient();
    const { data, isLoading, isFetching} = useQuery<IExamResponse | z.infer<typeof formData.schema>>({ queryKey: ['exam'], queryFn: formData.defaultValues });

    const { data: seriesData } = useQuery({
        queryKey: ['series'],
        queryFn: () => getSeries(),
    });

    const { form, resetForm } = useQuestions()

    console.log(form.watch());
    console.log(form.formState.errors);
    
    useEffect(() => {
        if (data && !isEmpty(data)) {
            const transformDateStringInDate = { 
                ...data, 
                start_date: new Date(data.start_date), 
                end_date: new Date(data.end_date),
                questions: data.questions.map((q: IQuestion) => ({
                    ...q,
                    data: q.data || '',
                    formatted_data: q.formatted_data || '',
                    theme: q.theme ?? null,
                    answers: Array.isArray(q.answers) ? q.answers : []
                }))
            };
            const newData = Object.assign({}, transformDateStringInDate);

            form.reset(newData)
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data]);

    const watchQuestions = form.watch('questions')
    const { errors } = form.formState

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await updateExamById(data.id, values);
            resetForm()
            setOpen(false)
        } catch (error) {
            toast.error(t('toast.errors.form.edit_exam'))
        } finally {
            setLoading(false)
        }
        queryClient.invalidateQueries({ queryKey: ['exams'] });
    }

    const handleSelectDay = (day: Date | undefined, onChange:any) => {
        if (day) {
            setStartDate(day)
        }
        onChange(day)
    }

    if ( !data || isEmpty(data) || isLoading || isFetching ) { return <SkeletonSheet/> }

    const today = new Date();
    const start_date = new Date(data.start_date);
    start_date.setMinutes(start_date.getMinutes() - 30); // to allow a quick edition until 30 minutes before exam start date
    const isEditable = today <= start_date;

    const renderField = (fieldName: string) => {
        if (fieldName === 'id') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName as any}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.exam.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.exam.edit.${field.name}`)}
                                    type={"text"}
                                    disabled={true}
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

        if (fieldName === 'name') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => (
                        <FormItem className="space-y-2">
                            <FormLabel>{t(`form.exam.edit.${field.name}`)}</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder={t(`form.exam.edit.${field.name}`)}
                                    type={"text"}
                                    disabled={!isEditable || preview}
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
                <FormQuestions isEditable={isEditable} preview={preview} />
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
                                        <SelectValue placeholder={t(`form.exam.edit.${field.name}`)} />
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
                            <FormLabel>{t(`form.exam.edit.${field.name}`)}</FormLabel>
                            <Popover>
                                <FormControl>
                                    <PopoverTrigger asChild>
                                        <Button
                                            disabled={!isEditable || preview}
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
                                        selected={field.value}
                                        onSelect={fieldName === 'start_date' ? (day) => handleSelectDay(day, field.onChange) : field.onChange}
                                        initialFocus
                                        fromDate={fieldName === 'start_date' ? new Date() : startDate} 
                                        locale={locale === 'es-ES' ? es : locale === 'en-US' ? enUS : ptBR}
                                    />
                                    <div className="p-3 border-t border-border dark:border-darkBorder">
                                        <TimePicker
                                            setDate={field.onChange}
                                            date={field.value}
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
                        {Object.keys(SchemaEditExamDefaultValues).map((fieldName) => {
                            return (
                                <fieldset key={fieldName} className="field-item w-full">
                                    {renderField(fieldName)}
                                </fieldset>
                            );
                        })}
                    </div>

                    <div className="flex w-full gap-4 items-center">
                        <div className="flex w-full gap-2 items-center">
                            <Button type="submit" variant={"secondary"} className="w-full" disabled={loading || preview}>
                                { !loading ?  t('form.exam.edit.confirm') : <Loading style="horizontal" text={true} size={16}/>}
                            </Button>
                            {watchQuestions && watchQuestions.find((q: IQuestion)=> !isEmpty(q.data)) && (
                                <QuestionPreview questions={watchQuestions}/>   
                            )}
                        </div>
                    </div>
                    {!loading && (
                        <Button variant="destructive" type="button" onClick={()=> setOpen(false)} className="w-full">
                            {preview ? t('form.exam.close') : t('form.exam.create.cancel')}
                        </Button>
                    )}
                </form>
            </Form>
        </>
    )
}

export default FormEditExam;