import React, { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { ControllerRenderProps, useController, useForm, UseFormReturn } from 'react-hook-form';

import { IAnswer, IQuestion, IQuestionEditor } from '@/interfaces/question';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { SchemaCreateExam, SchemaCreateExamDefaultValues, SchemaEditExam, SchemaEditExamDefaultValues } from '@/forms/exam/schema';
import { useCrudStore } from '@/store/crud';
import { ICrudStore } from '@/interfaces/store';
import { TElement } from '@udecode/plate-common';
import { useLoading } from './loading';
import { QuestionTheme, QuestionType, THIRD_HIGH_SCHOOL } from '@/constants/enums';
import { addDays } from 'date-fns';
import { getMultipleChoiceQuestion, getQuestions, getTextQuestion, getWordsQuestion } from '@/services/questions';

type TQuestionsProvider = {
    children: ReactNode,
    type: "create" | "edit" | "delete" | "import" | "view"
}

interface IQuestionsContext {
    type: "create" | "edit" | "delete" | "import" | "view"
    form: UseFormReturn<any, any, undefined>
    useReference: boolean
    setUseReference: (useReference: boolean) => void
    handleChangeQuestionType: (type: string, value: any, order: number) => void
    handleChangeQuestionTheme: (theme: QuestionTheme, value: any, order: number) => void
    handleWordsChange: (text: string, type: string, order: number) => void
    handlePhrasesChange: (value: { data: string; formatted_data: string }, type: string, order: number) => void
    handleMultipleChoiceChange: (value: { data: string; formatted_data: string }, order: number) => void
    handleAnswersChange: (answers :  IAnswer[], order: number) => void
    resetForm: () => void
    generateTextQuestion: (value: { subject: string, questionType: string, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[], order: number }) => void,
    generateMultipleChoiceQuestion: (value: { subject: string, order: number, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[] }) => void
    setAnswersQuantity: React.Dispatch<React.SetStateAction<number>>
    setReference: React.Dispatch<React.SetStateAction<string>>
    setBlockedQuestions: React.Dispatch<React.SetStateAction<string[]>>
    generateWordsQuestion: (question: IQuestionEditor, quantity: number) => void,
    generateQuestions: (value: { subject: string, questionType: string, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[], order: number, theme?: QuestionTheme }) => void
}

const QuestionsContext = createContext<IQuestionsContext>({} as IQuestionsContext);

const QuestionsProvider: React.FC<TQuestionsProvider> = ({ children, type }) => {
    const [ answersQuantity, setAnswersQuantity ] = useState<number>(5)
    const [ reference, setReference ] = useState<string>('')
    const [ blockedQuestions, setBlockedQuestions ] = useState<string[]>([])
    const [ useReference, setUseReference ] = useState<boolean>(true)
    const { setCRUD, exam } : ICrudStore = useCrudStore();
    const { setLoading } = useLoading()

    const createForm = useForm<z.infer<typeof SchemaCreateExam>>({
        resolver: zodResolver(SchemaCreateExam),
        defaultValues: exam ? {
            ...exam,
            grade: THIRD_HIGH_SCHOOL,
            start_date: addDays(new Date(), 1),
            end_date: addDays(new Date(), 8),
            questions: []
        } : SchemaCreateExamDefaultValues
    })

    const editForm = useForm<z.infer<typeof SchemaEditExam>>({
        resolver: zodResolver(SchemaEditExam),
        defaultValues: SchemaEditExamDefaultValues
    })

    const getFormByType = () => {
        switch (type) {
            case 'create':
                return createForm;
            case 'edit':
                return editForm;
            case 'view':
                return editForm;
            default:
                return createForm;
        }
    };
    
    const form = getFormByType();
    const { control } = form;
    const { name, questions, grade, start_date, end_date } = form.getValues()

    const { field } = useController<z.infer<typeof SchemaCreateExam>>({
        name: "questions",
        control: control as any
    });

    const handleChangeQuestionType = (type: string, value: ControllerRenderProps<any, any>, order: number) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], value);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === order);
        if (!newQuestion) return;
        newQuestion.name = type;
        newQuestion.type = type;
        field.onChange(newQuestions);
    }

    const handleChangeQuestionTheme = (theme: QuestionTheme, value: ControllerRenderProps<any, any>, order: number) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], value);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === order);
        if (!newQuestion) return;
        newQuestion.theme = theme;
        field.onChange(newQuestions);
    }

    const handleWordsChange = (text: string, type: string, order: number) => {
        const value = text.replace(/\s+/g, ' ');
        const newQuestions : Array<IQuestionEditor> = Object.assign([], questions);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.type === type && q.order === order);
        if (!newQuestion) return;
        newQuestion.data = value;
        newQuestion.formatted_data = value;
        field.onChange(newQuestions);
    }

    const handlePhrasesChange = async (value: { data: string; formatted_data: string }, type: string, order: number) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], questions);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.type === type && q.order === order);
        if (!newQuestion) return;
        
        newQuestion.data = value.data;
        newQuestion.formatted_data = value.formatted_data;
        field.onChange(newQuestions);
    }

    const handleMultipleChoiceChange = (value: { data: string; formatted_data: string }, order: number) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], questions);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === order);
        if (!newQuestion) return;

        newQuestion.data = value.data;
        newQuestion.formatted_data = value.formatted_data;
        field.onChange(newQuestions);
    }

    const handleAnswersChange = (answers :  IAnswer[], order: number) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], questions);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === order);
        if (!newQuestion) return;
        
        newQuestion.answers = answers;
        field.onChange(newQuestions);
    }

    const formatGeneratedText = (text: string) => {
        const formattedText = text.split('\n\n').map((paragraph, index) => ({  
            id: index.toString(),
            type: 'p',
            align: 'left',
            children: [{ text: paragraph }],
        }));

        return formattedText
    }

    const generateWordsQuestion = async (question: IQuestionEditor, quantity: number)=>{
        setLoading(true)

        let includedWords: string[] = []

        const words = question.data.replace(/\s+/g, ' ').trim().split(" ");

        if (questions) {
            if (questions[0].data.length > 0) {
                const questionWords = questions[0].data.replace(/\s+/g, ' ').trim().split(" ")
                includedWords = [...questionWords ]
            }

            if (questions[1].data.length > 0) {
                const questionWords = questions[1].data.replace(/\s+/g, ' ').trim().split(" ")
                includedWords = [...questionWords ]
            }
        }
        
        if (words.length > 0) {
            includedWords = [...includedWords, ...words]
        }

        try {
            const res = await getWordsQuestion(quantity, includedWords, question.type as QuestionType)
            const resWords = res.words.join(" ")

            handleWordsChange(`${question.data}${question.data.length > 0 ? ' ' : ''}${resWords}`, question.type, question.order as number)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    const generateTextQuestion = async ({ subject, questionType, setInitialValue, setKey, initialValue, order }: { subject: string, questionType: string, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[], order: number }) => {
        setLoading(true)

        try {
            const res = await getTextQuestion(subject)
            const decoder = new TextDecoder("utf-8");
            const fixedText = decoder.decode(new TextEncoder().encode(res));

            const formattedText = formatGeneratedText(fixedText)

            setInitialValue(formattedText)
            setKey(prev => prev + 1)

            const v = JSON.stringify(formattedText)
            const i = JSON.stringify(initialValue)

            if (v !== i) {
                const data = formattedText.map((children: TElement) => children.children[0].text).join(' ').replace(/\s+/g, ' ')
                const formatted_data = JSON.stringify(formattedText)
                handlePhrasesChange({data, formatted_data}, questionType, order)
            }
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    const generateQuestions = async ({ subject, questionType, setInitialValue, setKey, initialValue, order, theme = null }: { subject: string, questionType: string, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[], order: number, theme?: QuestionTheme | null }) => {
        setLoading(true)

        try {
            const ref = useReference ? reference : ''

            const res = await getQuestions(questionType, subject, ref, blockedQuestions, theme)
            const decoder = new TextDecoder("utf-8");
            const fixedText = decoder.decode(new TextEncoder().encode(res.question));

            const formattedText = formatGeneratedText(fixedText)

            setInitialValue(formattedText)
            setKey(prev => prev + 1)

            const v = JSON.stringify(formattedText)
            const i = JSON.stringify(initialValue)

            if (v !== i) {
                const data = formattedText.map((children: TElement) => children.children[0].text).join(' ').replace(/\s+/g, ' ')
                const formatted_data = JSON.stringify(formattedText)
                handlePhrasesChange({data, formatted_data}, questionType, order)
            }
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    const generateMultipleChoiceQuestion = async ({ subject, order, setInitialValue, setKey, initialValue }: { subject: string, order: number, setInitialValue: React.Dispatch<React.SetStateAction<TElement[]>>, setKey: React.Dispatch<React.SetStateAction<number>>, initialValue: TElement[] }) => {
        setLoading(true)

        try {
            const ref = useReference ? reference : ''

            const res = await getMultipleChoiceQuestion(answersQuantity, subject, ref, blockedQuestions)

            const decoder = new TextDecoder("utf-8");
            const fixedText = decoder.decode(new TextEncoder().encode(res.question));

            const formattedText = formatGeneratedText(fixedText)

            setInitialValue(formattedText)
            setKey(prev => prev + 1)

            const v = JSON.stringify(formattedText)
            const i = JSON.stringify(initialValue)

            if (v !== i) {
                const data = formattedText.map((children: TElement) => children.children[0].text).join(' ').replace(/\s+/g, ' ')
                const formatted_data = JSON.stringify(formattedText)
                handleMultipleChoiceChange({data, formatted_data}, order)
                handleAnswersChange(res.answers, order)
            }

        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(()=>{
        if (getFormByType() === createForm) {
            if (questions && questions.length > 0 && questions[0].data) {
                setCRUD('exam', {name, questions, grade, start_date, end_date})
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    },[name, questions, grade, start_date, end_date, setCRUD])

    const resetForm = ()=> {
        setCRUD('exam', SchemaCreateExamDefaultValues)
    }

    return (
        <QuestionsContext.Provider value={{ 
            type,
            form, 
            useReference, 
            setUseReference, 
            handleChangeQuestionType, 
            handleWordsChange, 
            handlePhrasesChange, 
            handleMultipleChoiceChange, 
            handleAnswersChange, 
            resetForm, 
            generateTextQuestion, 
            generateMultipleChoiceQuestion, 
            setAnswersQuantity,
            setReference,
            setBlockedQuestions,
            generateWordsQuestion,
            generateQuestions,
            handleChangeQuestionTheme
        }}>
            {children}
        </QuestionsContext.Provider>
    );
};

const useQuestions = () => {
    const context = useContext(QuestionsContext);
    if (!context) {
        throw new Error('useQuestions must be used within a QuestionsProvider');
    }
    return context;
};

export { QuestionsProvider, useQuestions };
