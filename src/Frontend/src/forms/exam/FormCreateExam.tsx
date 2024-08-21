import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { ptBR, enUS, es } from "date-fns/locale";
import { TFormCreateProps } from "@/interfaces/component";
import { useQueryClient } from "@tanstack/react-query";
import { createExam } from "@/services/exam";
import { getFormattedDate } from "@/utils";

import QuestionsEditor from "@/components/visors/QuestionsEditor";
import QuestionPreview from "@/components/question-preview/QuestionsPreview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTrigger, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { CalendarIcon, LucideCircleCheck, LucideCircleX } from "lucide-react";
import { cn } from "@/libs/shadcn/utils";
import { ENUM_GRADE_OPTIONS, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE } from '@/constants/enums'
import { IAnswer, IQuestion, IQuestionEditor } from "@/interfaces/question";
import { isEmpty } from "lodash";
import { TimePicker } from "@/components/ui/time-picker";
import { ICrudStore } from "@/interfaces/store";
import { useCrudStore } from "@/store/crud";
import { toast } from "react-toastify";
import Loading from "@/components/loading/Loading";
import { useLoading } from "@/context/loading";

const FormCreateExam : React.FC<TFormCreateProps> = ({ formData, setOpen }) => {
    const [startDate, setStartDate] = useState<Date>(new Date());
    const { loading, setLoading } = useLoading()

    const t = useTranslations();
    const { locale } = useParams();
    const queryClient = useQueryClient();
    const { setCRUD, exam } : ICrudStore = useCrudStore();
    const form = useForm<z.infer<typeof formData.schema>>({
        resolver: zodResolver(formData.schema),
        defaultValues: exam || formData.defaultValues
    })

    const [watchQuestions, watchName, watchGrade, watchStartDate, watchaEndDate] = form.watch(['questions','name','grade','start_date','end_date' ])

    useEffect(()=>{
        setCRUD('exam', {name: watchName, questions: watchQuestions, grade: watchGrade, start_date: watchStartDate, end_date: watchaEndDate})
    // eslint-disable-next-line react-hooks/exhaustive-deps
    },[watchQuestions, watchName, watchGrade, watchStartDate, watchaEndDate, setCRUD])

    const resetForm = ()=> {
        setCRUD('exam', formData.defaultValues)
    }

    const onSubmit = async (values: z.infer<typeof formData.schema>) => {
        setLoading(true)
        try {
            await createExam(values);
            toast.success(t('toast.success.form.exam_created'))
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
                            <FormMessage />
                        </FormItem>
                    )}
                />
            )
        }

        if (fieldName === 'questions') {
            return (
                <FormField
                    control={form.control}
                    name={fieldName}
                    render={({ field }) => {

                        let order = field.value.length + 1

                        const emptyQuestion = {
                            order,
                            name: ENUM_QUESTION_TYPE_MULTIPLE_CHOICE,
                            type: ENUM_QUESTION_TYPE_MULTIPLE_CHOICE,
                            data: '',
                            formatted_data: '',
                            answers: []
                        }

                        const handleAddQuestion = ()=>{
                            const lastQuestion = field.value[field.value.length - 1]
                            if (lastQuestion.order > 3 && lastQuestion.answers.length < 2) {
                                toast.error(t("toast.errors.form.empty_question"));
                                return
                            }

                            const check = lastQuestion?.answers?.some((item: IAnswer) => item.is_correct === true )

                            if (!check && field.value.length > 3) {
                                toast.error(t("toast.errors.form.missing_true"));
                                return
                            }

                            field.onChange([...field.value, emptyQuestion]);
                        }

                        const handleDeleteQuestion = (order: number) => {
                            const updatedData = field.value.filter((v: {order: number}) => v.order !== order)

                            field.onChange(updatedData)
                        }

                        return (
                            <FormItem className="space-y-2 flex flex-col items-start">
                                <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                                <FormControl>
                                    <div className="flex flex-col gap-1 w-full max-[300px]">
                                        {field.value.map((question: IQuestionEditor, index: number) => (
                                            <Dialog key={index}>
                                                <DialogTrigger className="py-2 px-4 border dark:border-darkBorder dark:text-white rounded-md text-sm w-full text-start">
                                                    <div className="flex w-full justify-between items-center">
                                                        <span>{question.type === ENUM_QUESTION_TYPE_MULTIPLE_CHOICE ? t(`form.exam.${question.type}`) + ` ${question.order && (question.order - 3)}` : t(`form.exam.create.${question.type}`)}</span>
                                                        <i>
                                                            {!isEmpty(question.data) ? 
                                                                <LucideCircleCheck className="w-5 h-5 text-green-500" />
                                                                : 
                                                                <LucideCircleX className="w-5 h-5 text-destructive dark:text-darkDestructive" />
                                                            }
                                                        </i>
                                                    </div>
                                                </DialogTrigger>
                                                <DialogContent style={{maxWidth: '1024px', minWidth: '90%', width: '90%'}}>
                                                    <p className="dark:text-white">{t(`form.exam.${question.type}`)}</p>
                                                    <QuestionsEditor 
                                                        question={question} 
                                                        field={field} 
                                                        index={index} 
                                                    />
                                                    <div className="w-full flex justify-end gap-4">
                                                        {question.type === 'multiple_choice' && (
                                                            <Dialog>
                                                                <DialogTrigger asChild>
                                                                    <Button type="button" variant="secondary" className="w-max bg-destructive dark:bg-darkDestructive hover:bg-destructive/75 hover:dark:bg-darkDestructive/75">
                                                                        {t('form.exam.delete_question_button')}
                                                                    </Button>
                                                                </DialogTrigger>
                                                                <DialogContent className="sm:max-w-[425px]">
                                                                    <DialogHeader>
                                                                        <DialogTitle className="dark:text-white">{t('form.exam.delete_question_title')}</DialogTitle>
                                                                        <DialogDescription>{t('form.exam.delete_question_description')}</DialogDescription>
                                                                    </DialogHeader>
                                                                    <DialogFooter>
                                                                        <DialogClose asChild>
                                                                            <Button type="button" variant="secondary">
                                                                                {t('form.exam.close')}
                                                                            </Button>
                                                                        </DialogClose>
                                                                     
                                                                        <Button type="button" className="bg-destructive dark:bg-darkDestructive hover:bg-destructive/75 hover:dark:bg-darkDestructive/75" onClick={()=>handleDeleteQuestion(question.order as number)}>{t('form.exam.delete_confirm')}</Button>
                                                                       
                                                                    </DialogFooter>
                                                                </DialogContent>
                                                            </Dialog>
                                                        )}
                                                        <DialogClose asChild>
                                                            <Button type="button" variant="secondary" className="w-max">
                                                                {t('form.exam.create.confirm')}
                                                            </Button>
                                                        </DialogClose>
                                                    </div>
                                                </DialogContent>
                                            </Dialog>  
                                        ))} 
                                        <div className="w-full flex justify-end space-y-2">
                                            <Button type="button" onClick={handleAddQuestion}>{t('form.exam.add_question')}</Button>
                                        </div>
                                    </div>
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )
                    }}
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
                                    {ENUM_GRADE_OPTIONS.map((option, index) => (
                                        <SelectItem key={index} value={option.value}>
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
                        {Object.keys(formData.defaultValues).map((fieldName) => {
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
                            {watchQuestions && watchQuestions.find((q: IQuestion)=> !isEmpty(q.data)) && (
                                <QuestionPreview questions={watchQuestions}/>   
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