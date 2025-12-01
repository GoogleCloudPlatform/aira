import React, { useEffect, useState } from 'react'
import { FormControl, FormField, FormItem, FormLabel } from '@/components/ui/form'
import { QuestionTheme, QuestionType } from '@/constants/enums'
import { useTranslations } from 'next-intl'
import { IQuestionEditor } from '@/interfaces/question'
import { Button } from '@/components/ui/button'
import { useQuestions } from '@/context/questions'
import QuestionDialog from './question-dialog/QuestionDialog'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useLoading } from '@/context/loading'

interface IFormQuestions {
    isEditable?: boolean
    preview?: boolean
}

const FormQuestions: React.FC<IFormQuestions> = ({ isEditable = true, preview = false }) => {
    const [type, setType] = useState<QuestionType | 'proficiency'>('proficiency')

    const t = useTranslations()
    const { form } = useQuestions()
    const { loading } = useLoading()

    const { errors } = form.formState

    const questions = form.watch('questions')
    
    const industryAreasQuestions = questions.filter((question: IQuestionEditor) => question.type === QuestionType.IndustryAreas)
    const lastTheme = industryAreasQuestions.length > 0 ? industryAreasQuestions[industryAreasQuestions.length - 1].theme : QuestionTheme.MonicaAguaBoa

    useEffect(() => {
        if (type === 'proficiency' && questions.length > 0) {   
            setType(QuestionType.IndustryAreas)
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [questions])

    return (
        <FormField
            control={form.control}
            name={'questions'}
            render={({ field }) => {
                let order = field.value.length + 1

                const emptyQuestion = {
                    order,
                    name: type,
                    type: type,
                    theme: type === QuestionType.IndustryAreas ? lastTheme ? lastTheme : QuestionTheme.MonicaAguaBoa : null,
                    data: '',
                    formatted_data: '',
                    answers: []
                }

                const wordQuestion = {
                    order: 1,
                    name: QuestionType.Words,
                    type: QuestionType.Words,
                    theme: null,
                    data: '',
                    formatted_data: '',
                    answers: []
                }

                const complexWordsQuestion = {
                    order: 2,
                    name: QuestionType.ComplexWords,
                    type: QuestionType.ComplexWords,
                    theme: null,
                    data: '',
                    formatted_data: '',
                    answers: []
                }

                const phrasesQuestion = {
                    order: 3,
                    name: QuestionType.Phrases,
                    type: QuestionType.Phrases,
                    theme: null,
                    data: '',   
                    formatted_data: '',
                    answers: []
                }   

                const handleAddQuestion = ()=>{
                    if (type === 'proficiency' && field.value.length === 0) {   
                        field.onChange([wordQuestion, complexWordsQuestion, phrasesQuestion]);
                        setType(QuestionType.IndustryAreas)
                    } else {
                        field.onChange([...field.value, emptyQuestion]);
                    }
                }

                const defaultOptions = [QuestionType.IndustryAreas, QuestionType.MultipleChoice, QuestionType.LogicalSituations, QuestionType.UnderstantindCheck, QuestionType.ShortExplanations]

                const options = field.value.length === 0 ? ['proficiency', ...defaultOptions] : defaultOptions

                return (
                    <FormItem className="space-y-2 flex flex-col items-start">
                        <FormLabel>{t(`form.exam.create.${field.name}`)}</FormLabel>
                        <FormControl>
                            <div className="flex flex-col gap-1 w-full max-[300px]">
                                {field.value.length === 0 ? (
                                    <div className='text-center text-sm text-gray-500 w-full px-4 py-2 border border-dashed border-gray-300 rounded-md'>
                                        {t('form.exam.select_question_type')}
                                    </div>
                                ) : field.value.map((question: IQuestionEditor, index: number) => (
                                    <QuestionDialog key={index} question={question} field={field} index={index} isEditable={isEditable} preview={preview} />
                                ))} 

                                {!preview && (
                                    <div className="w-full flex justify-between items-center gap-2 my-2">
                                        <Select 
                                            onValueChange={(value) => setType(value as QuestionType)} 
                                            value={type}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder={t('form.exam.question_type')} />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectGroup>
                                                    {options.map(value => 
                                                        <SelectItem key={value} value={value}>
                                                            {t(`form.exam.${value}`)}
                                                        </SelectItem>
                                                    )}
                                                </SelectGroup>
                                            </SelectContent>
                                        </Select>

                                        <Button disabled={loading || preview} type="button" onClick={handleAddQuestion}>{t('form.exam.add_question')}</Button>
                                    </div>
                                )}
                            </div>
                        </FormControl>
                        {errors[field.name] && (
                            <span className="text-red-500 text-sm">{errors[field.name]?.message && t(errors[field.name]?.message?.toString())}</span>
                        )}
                    </FormItem>
                )
            }}
        />
    )
}

export default FormQuestions
