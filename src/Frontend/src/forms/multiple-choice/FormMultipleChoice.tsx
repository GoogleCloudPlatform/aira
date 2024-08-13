import React, { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useLoading } from '@/context/loading';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { useExamsStore } from '@/store/exams';
import { useRecordStore } from '@/store/record';
import { useRBAC } from '@/context/rbac';
import { IAnswer, IQuestionEditor } from '@/interfaces/question';
import { SchemaMultipleChoiceAnswer, SchemaMultipleChoiceDefaultValues } from './schema';
import { sendMultipleChoiceAnswer } from '@/services/exam';
import { SCOPE_USER } from '@/constants/rbac';
import { MAX_RECORD_SECONDS } from '@/constants/exams';
import { IExamsStore, IRecordStore } from '@/interfaces/store';

import Loading from '../../components/loading/Loading';
import { Checkbox } from '../../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../../components/ui/radio-group';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '../../components/ui/form';
import { Button } from '../../components/ui/button';

type TAnswerVisorProps = {
    question: IQuestionEditor;
    total_questions: number;
}

const FormMultipleChoice : React.FC<TAnswerVisorProps> = ({ question, total_questions }) => {
    const [shuffledAnswers, setShuffledAnswers] = useState<IAnswer[]>([]);
    const correctAnswersArray = question?.answers?.filter( answer => answer.is_correct === true)
    const singleAnswer = correctAnswersArray?.length === 1 ? true : false
    
    const t = useTranslations()
    const router = useRouter()
    const params = useParams()
    const queryClient = useQueryClient()
    const { loading, setLoading } = useLoading()
    const { questionIndex, setExams } : IExamsStore = useExamsStore()
    const { setRecord } : IRecordStore = useRecordStore();
    const { hasScopePermission } = useRBAC();

    const isStudent = hasScopePermission([SCOPE_USER]);
    const exam_id = params.id as string
    const user_id = params.user_id as string
    const question_id = question.id as string

    const form = useForm<z.infer<typeof SchemaMultipleChoiceAnswer>>({
        resolver: zodResolver(SchemaMultipleChoiceAnswer),
        defaultValues: SchemaMultipleChoiceDefaultValues
    });

    useEffect(() => {
        if (question?.answers) {
            const shuffled = [...question.answers].sort(() => Math.random() - 0.5);
            setShuffledAnswers(shuffled);
        }
    }, [question]);

    
    const endExam = useCallback(() => {
        setLoading(true)
        setExams("expanded", false);
        setRecord("audioURL", "");
        setRecord("audioChunks", []);
        setRecord("canStop", false);
        setRecord("seconds", MAX_RECORD_SECONDS);
        
        if (isStudent) {
            router.push(`/exams/${exam_id}/finish`);
            return; 
        }
        
        router.push(`/users/${user_id}/exams/${exam_id}/finish`);
    }, [setExams, setRecord, setLoading, isStudent, router, exam_id, user_id]);

    if (!exam_id || !user_id || !question_id) return null
    if (!question.answers) return null

    const onSubmit = async ({answers}: z.infer<typeof SchemaMultipleChoiceAnswer>)=>{
        try {
            await sendMultipleChoiceAnswer( {exam_id , user_id, question_id, answers })
            
            const hasNextQuestion = questionIndex < total_questions - 1;
            if (!hasNextQuestion) return endExam()
                
            setExams("questionIndex", questionIndex + 1)
            queryClient.invalidateQueries({ queryKey: ['questions'] });
        } catch (error) {
            console.log(error)
        }
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-2">
                {singleAnswer ? (
                    <FormField
                        control={form.control}
                        name="answers"
                        render={({ field }) => (
                            <FormItem className="space-y-3">
                                <FormLabel>{t(`form.multiple_choice.options`)}</FormLabel>
                                <FormControl>
                                    <RadioGroup
                                        onValueChange={value => {
                                            field.onChange([value])
                                        }}
                                        className='flex flex-col gap-1'
                                    >
                                        {shuffledAnswers.map((item, index) => (
                                            <FormItem key={index} className='dark:text-white flex items-center gap-3 p-2 bg-gray-100 dark:bg-darkPrimary/20 rounded min-h-10'>
                                                <FormControl className='w-4 h-4'>
                                                    <RadioGroupItem value={item.answer} className='w-4 h-4'/>
                                                </FormControl>
                                                <FormLabel className="!mt-0 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 overflow-hidden break-words h-max">
                                                    {item.answer}
                                                </FormLabel>
                                            </FormItem>
                                        ))}
                                    
                                    </RadioGroup>
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />
                ): (
                    <FormField
                        control={form.control}
                        name="answers"
                        render={() => (
                            <FormItem>
                                <FormLabel>{t(`form.multiple_choice.options`)}</FormLabel>
                                {shuffledAnswers.map((item, index) => (
                                    <FormField
                                        key={item.answer}
                                        control={form.control}
                                        name={`answers`}
                                        render={({ field }) => {
                                            return (
                                                <FormItem
                                                    key={index}
                                                    className="dark:text-white flex items-center gap-6 p-2 bg-gray-100 dark:bg-darkPrimary/20 rounded min-h-10"
                                                >
                                                    <FormControl>
                                                        <Checkbox
                                                            checked={field.value?.includes(item.answer)}
                                                            onCheckedChange={(checked) => {
                                                                return checked
                                                                    ? field.onChange([...field.value, item.answer])
                                                                    : field.onChange(
                                                                        field.value?.filter(
                                                                            (value) => value !== item.answer
                                                                        )
                                                                    )
                                                            }}
                                                        />
                                                    </FormControl>
                                                    <FormLabel className="!mt-0 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 overflow-hidden break-words h-max">
                                                        {item.answer}
                                                    </FormLabel>
                                                </FormItem>
                                            )
                                        }}
                                    />
                                ))}
                                <FormMessage />
                            </FormItem>
                        )}
                    />
                )}

                <div className="flex w-full gap-2 justify-end">
                    <Button type="submit" variant={"secondary"} disabled={loading}>
                        { !loading ?  t('form.multiple_choice.submit') : <Loading style="horizontal" text={true} size={16}/>}
                    </Button>
                </div>
            </form>
        </Form>
        
    )
}

export default FormMultipleChoice