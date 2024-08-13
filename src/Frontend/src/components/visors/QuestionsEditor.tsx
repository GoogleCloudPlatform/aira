import React from 'react'
import { Textarea } from '@/components/ui/textarea'
import { IAnswer, IQuestion, IQuestionEditor } from '@/interfaces/question'
import { QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_PHRASES } from '@/constants/exams'
import { isEmpty } from 'lodash'
import { ControllerRenderProps } from 'react-hook-form'
import { useTranslations } from 'next-intl'
import TextEditor from '../text-editor/TextEditor'
import AnswersEditor from '../answers/AnswersEditor'
import { XIcon } from 'lucide-react'

type TQuestionEditorProps = {
    question: IQuestionEditor;
    field: ControllerRenderProps<any, "questions">;
    index: number;
}

type TQuestionEditorWordsProps = {
    question: IQuestionEditor;
    onChange: (text: string) => void;
    maxLength: number;
}

const QuestionsEditorWords : React.FC<TQuestionEditorWordsProps> = ({ question, onChange, maxLength }) => {
    const t = useTranslations();
    const shouldDisplay = !isEmpty(question.data);
    const words = question.data.replace(/\s+/g, ' ').trim().split(" ");

    const removeWord = (word: string) => {
        const questionArr = question.data.split(' ')
        const remove = questionArr.filter( q => q !== word)
        const setNewText = remove.join(' ')
        onChange(setNewText)
    }
    
    if (!words) return null;

    return  ( 
        <div className="flex flex-col gap-4">
            <Textarea
                placeholder={t(`text-editor.editor.${question.name}`)}
                value={question.data}
                onChange={(e)=>onChange(e.target.value)}
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
                <div className='w-full flex justify-between dark:text-white -mt-1 pr-6 text-xs'>
                    <p className={`${words.length >= maxLength && 'text-destructive dark:text-darkDestructive'}`}>
                        {`${t('text-editor.editor.total')}`} {`(${words.length})`}
                    </p>
                </div>
            )}
        </div>
    );
}

const QuestionsEditor: React.FC<TQuestionEditorProps> = ({ question, field, index }) => {
    if (!question) return null;
    
    const question_type = question.type;

    const handleWordsChange = (text: string) => {
        const value = text.replace(/\s+/g, ' ');
        const newQuestions : Array<IQuestion> = Object.assign([], field.value);
        const newQuestion = newQuestions.find((q: IQuestion) => q.type === question.type);
        if (!newQuestion) return;
        newQuestion.data = value;
        newQuestion.formatted_data = value;
        field.onChange(newQuestions);
    }

    const handlePhrasesChange = (value: { data: string; formatted_data: string }) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], field.value);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.type === question.type);
        if (!newQuestion) return;
        
        newQuestion.data = value.data;
        newQuestion.formatted_data = value.formatted_data;
        field.onChange(newQuestions);
    }

    const handleMultipleChoiceChange = (value: { data: string; formatted_data: string }) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], field.value);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === question.order);
        if (!newQuestion) return;
        
        newQuestion.data = value.data;
        newQuestion.formatted_data = value.formatted_data;
        field.onChange(newQuestions);
    }

    const handleAnswersChange = (answers :  IAnswer[]) => {
        const newQuestions : Array<IQuestionEditor> = Object.assign([], field.value);
        const newQuestion = newQuestions.find((q: IQuestionEditor) => q.order === question.order);
        if (!newQuestion) return;
        
        newQuestion.answers = answers;
        field.onChange(newQuestions);
    }

    if (question_type === QUESTION_TYPE_PHRASES) {
        return (
            <TextEditor data={question.formatted_data} onChange={handlePhrasesChange} />
        );
    } 

    if (question_type === QUESTION_TYPE_MULTIPLE_CHOICE) {
        return (
            <>
                <TextEditor data={question.formatted_data} onChange={handleMultipleChoiceChange} />
                <AnswersEditor question={question} onChange={handleAnswersChange} />
            </>
        );
    } 

    return <QuestionsEditorWords question={question} onChange={handleWordsChange} maxLength={index === 1 ? 40 : 60}/>
}

export default QuestionsEditor;