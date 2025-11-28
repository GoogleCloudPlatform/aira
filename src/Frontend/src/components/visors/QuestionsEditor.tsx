import React, { useEffect, useState } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { IQuestionEditor } from '@/interfaces/question'
import { QUESTION_TYPE_MULTIPLE_CHOICE } from '@/constants/exams'
import { isEmpty } from 'lodash'
import { ControllerRenderProps } from 'react-hook-form'
import { useTranslations } from 'next-intl'
import TextEditor from '../text-editor/TextEditor'
import AnswersEditor from '../answers/AnswersEditor'
import { LoaderCircle, Sparkles, XIcon } from 'lucide-react'
import { useLoading } from '@/context/loading'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { QuestionTheme, QuestionType } from '@/constants/enums'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Switch } from '../ui/switch'
import { useQuestions } from '@/context/questions'

type TQuestionEditorProps = {
    question: IQuestionEditor;
    field: ControllerRenderProps<any, any>;
    index: number;
    preview?: boolean;
}

type TQuestionEditorWordsProps = {
    questions?: IQuestionEditor[];
    question: IQuestionEditor;
    maxLength: number;
}

const QuestionsEditorWords : React.FC<TQuestionEditorWordsProps> = ({ question, maxLength }) => {
    const { loading } = useLoading()
    const [ quantity, setQuantity ] = useState<number>(0)

    const {  handleWordsChange, generateWordsQuestion } = useQuestions()

    const t = useTranslations();
    const shouldDisplay = !isEmpty(question.data);
    const words = question.data.replace(/\s+/g, ' ').trim().split(" ");

    const removeWord = (word: string) => {
        const questionArr = question.data.split(' ')
        const remove = questionArr.filter( q => q !== word)
        const setNewText = remove.join(' ')
        handleWordsChange(setNewText, question.type, question.order as number)
    }

    if (!words) return null;

    return  ( 
        <div className="flex flex-col gap-4">
            <div className='w-full flex flex-col lg:flex-row justify-end gap-2'>
                <Input type='number' placeholder={t('form.exam.quantity')} onChange={(e)=> setQuantity(Number(e.target.value))} className='w-full lg:max-w-[185px] input-no-spinner'/>
                <Button type="button" disabled={loading || quantity === 0} onClick={() => generateWordsQuestion(question, quantity)} className='flex items-center gap-2 w-full lg:max-w-[185px]'> 
                    {loading ? (
                        <>
                            <LoaderCircle className={`animate-spin text-white`} size={20}/>
                            {t('form.exam.loading')}
                        </>
                    ) : (
                        <>
                            <Sparkles size={16} /> 
                            {t('form.exam.generate_words')}
                        </>
                    )}
                </Button>
            </div>
            <Textarea
                placeholder={t(`text-editor.editor.${question.name}`)}
                value={question.data}
                onChange={(e) => handleWordsChange(e.target.value, question.type, question.order as number)}
                className="resize-none min-h-[250px] max-h-[250px] dark:text-white"
                disabled={words.length >= maxLength && question.data[question.data.length - 1] === ' '}
            />
            <div className="grid grid-cols-4 w-full gap-2 overflow-y-auto max-h-[250px] pr-4 dark:text-white" 
            >
                {shouldDisplay && words.map((word:string, i: number) => (
                    <div
                        key={i} 
                        className="p-2 border border-border dark:border-darkBorder rounded-md overflow-hidden text-center min-h-[42px] flex items-center justify-between gap-2" 
                        style={{width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis'}}
                    >   
                        <span className='truncate uppercase text-xs'>
                            {word}
                        </span>
                       
                        <button type='button' onClick={()=>removeWord(word)}><XIcon size={14}/></button>
                    </div>
                ))}
            </div>
            {shouldDisplay && (
                <div className='w-full flex justify-between dark:text-white -mt-1 pr-6 text-xs font-bold'>
                    <p className={`${words.length > maxLength && 'text-destructive dark:text-darkDestructive'}`}>
                        {`${t('text-editor.editor.total')}`} {`(${words.length})`}
                    </p>
                </div>
            )}
        </div>
    );
}

const QuestionsEditor: React.FC<TQuestionEditorProps> = ({ question, field, index, preview = false }) => {
    const t = useTranslations();
    const { useReference, setUseReference, handleChangeQuestionType, handleChangeQuestionTheme, setReference, setBlockedQuestions } = useQuestions()

    const { form } = useQuestions()
    const { questions } = form.watch()

    useEffect(()=>{
        if (questions.length > 2 && questions[2].type === QuestionType.Phrases) {
            setReference(questions[2].data)
        } else {
            setReference('')
        }

        const blockedQuestions = questions.filter((q: IQuestionEditor, index: number) => index > 2).map((q: IQuestionEditor) => q.data).filter((q: string) => q.length > 0)

        setBlockedQuestions(blockedQuestions)
    }, [questions, setReference, setBlockedQuestions])

    useEffect(()=>{
        if (question.type && (question.type === QuestionType.LogicalSituations || question.type === QuestionType.ShortExplanations)) {
            setUseReference(false)
        }
    }, [question, setUseReference])
    
    if (!question) return null;
    
    const options = [ QuestionType.IndustryAreas, QuestionType.MultipleChoice, QuestionType.LogicalSituations, QuestionType.UnderstantindCheck, QuestionType.ShortExplanations]
    const question_type = question.type;

    if (question_type === QuestionType.Words || question_type === QuestionType.ComplexWords) {
        return <QuestionsEditorWords question={question} maxLength={index === 1 ? 40 : 60} />
    }

    if (question_type === QuestionType.Phrases) {
        return (
            <>  
                <TextEditor data={question.formatted_data} questionType={question_type} order={Number(question.order)} preview={preview} />
            </>
        );
    }

    if (question_type !== QuestionType.Phrases && question_type !== QuestionType.Words && question_type !== QuestionType.ComplexWords) {
        return (
            <>  
                <div className='flex justify-between items-center gap-2'>
                    <Select 
                        onValueChange={(type) => handleChangeQuestionType(type, field.value, Number(question.order))} 
                        defaultValue={question_type}
                        disabled={preview}
                    >
                        <SelectTrigger className="1/2">
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
                    
                    {question_type !== QuestionType.LogicalSituations && question_type !== QuestionType.ShortExplanations && question_type !== QuestionType.IndustryAreas && (
                        <div className='flex items-center gap-2'>
                            <span className='dark:text-white'>{useReference ? t('form.exam.use_reference') : t('form.exam.dont_use_reference')}</span>
                            <Switch
                                id='switch-use-reference'
                                checked={useReference}
                                onClick={() => setUseReference(!useReference)}
                                disabled={preview}
                            />
                        </div>
                    )}

                    {question_type === QuestionType.IndustryAreas && (
                        <Select 
                            onValueChange={(theme) => handleChangeQuestionTheme(theme as QuestionTheme, field.value, Number(question.order))} 
                            value={question.theme || QuestionTheme.FoodAndBeverages}
                            disabled={preview}
                        >
                            <SelectTrigger className="1/2">
                                <SelectValue placeholder={t('form.exam.theme')} />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    {Object.values(QuestionTheme).map((value: QuestionTheme) => 
                                        <SelectItem key={value} value={value}>
                                            {t(`form.exam.${value}`)}
                                        </SelectItem>
                                    )}
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    )}
                </div>
                
                <TextEditor data={question.formatted_data} questionType={question_type} order={Number(question.order)} preview={preview} theme={question.theme} />
                {question_type === QUESTION_TYPE_MULTIPLE_CHOICE && (
                    <AnswersEditor question={question} preview={preview} />
                )}
            </>
        );
    } 

    return null
}

export default QuestionsEditor;