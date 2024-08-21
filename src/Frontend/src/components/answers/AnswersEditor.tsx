import { IAnswer, IQuestionEditor } from '@/interfaces/question';
import { useTranslations } from 'next-intl';
import React, { useState } from 'react'
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { LucideCircleCheck, LucideCircleX, LucideEdit, LucideTrash } from 'lucide-react';
import { toast } from 'react-toastify';

type TAnswerEditorProps = {
    question: IQuestionEditor;
    onChange: (answers: IAnswer[]) => void
}

const AnswersEditor : React.FC<TAnswerEditorProps> = ({ question, onChange }) => {
    const [editState, setEditState] = useState<{index: number | null, isEditing: boolean}>({index: null, isEditing: false})
    const [answer, setAnswer] = useState<IAnswer>({
        answer: '',
        is_correct: false
    })

    const t = useTranslations()

    const handleClear = () => {
        setAnswer({
            answer: '',
            is_correct: false
        })
        setEditState({index: null, isEditing: false})
    }

    const handleAddAnswer = ()=>{
        if (!question.answers) return
        if (question.answers.length >= 5 ) {
            toast.error(t("toast.errors.form.max_answers"));
            return
        }

        if (answer.answer.length === 0) {
            toast.error(t("toast.errors.form.answer_is_required"));
            return
        }

        const check = question.answers.find(a => a.answer.toLowerCase().trim() === answer.answer.toLocaleLowerCase().trim())

        if (check) {
            toast.error(t("toast.errors.form.answer_already_exists"));
            return
        }
        
        onChange([...question.answers, answer])
        handleClear()
    }
    
    const handleToggleOption = (index: number) => {
        if (!question.answers) return
        const answer = question.answers.find( (a,i) => i === index)
        if (!answer) return
        
        const toggleAnswer = {...answer, is_correct: !answer?.is_correct}
        
        const updateAnswers = question.answers.map( (a, i) => {
            if (i === index) return toggleAnswer
            
            return a
        } )
        
        onChange(updateAnswers)
    }
    
    const handleRemoveAnswer = (index: number) => {
        if (!question.answers) return
        
        const removeAnswer = question.answers.filter( (a, i) => i !== index )
        
        onChange(removeAnswer)
        handleClear()
    }
    
    const handleStartEdit = (index: number) => {
        if (!question.answers) return
        const answer = question.answers.find( (a,i) => i === index)
        if (!answer) return

        setAnswer(answer)
        setEditState({index: index, isEditing: true})
    }

    const handleEditAnswer = (index: number) => {
        if (!question.answers) return

        const check = question.answers.find(a => a.answer.toLowerCase().trim() === answer.answer.toLocaleLowerCase().trim())

        if (check) {
            toast.error(t("toast.errors.form.answer_already_exists"));
            return
        }
        
        const updateAnswers = question.answers.map( (a, i) => {
            if (i === index) return answer
            
            return a
        } )
        
        onChange(updateAnswers)
        handleClear()
    }

    if (!question.answers) return null
    
    return (
        <div className='flex flex-col gap-2'>
            <p className='dark:text-white'>{`${t('form.exam.answers')} (${question.answers?.length})`}</p>
            
            <ul className={` ${(question.answers?.length >= 5 && !editState.isEditing) ? 'max-h-[250px]' : 'max-h-[150px]'}  overflow-y-auto flex flex-col gap-1`}>
                {question.answers?.map((item, index) => (
                    <div key={index} className='dark:text-white flex items-center gap-6 p-2 bg-gray-100  dark:bg-darkPrimary/20 rounded'>
                        <div className='flex items-center gap-2'>
                            <Switch
                                id='switch-correct'
                                checked={item.is_correct}
                                onClick={() => handleToggleOption(index)}
                            />
                            <Label htmlFor="switch-correct">{item.is_correct ? <LucideCircleCheck className="w-5 h-5 text-green-500" /> : <LucideCircleX className="w-5 h-5 text-destructive dark:text-darkDestructive" />}</Label>
                        </div>

                        <span className='flex-1 overflow-x-hidden break-words'>
                            {item.answer} 
                        </span>

                        <div>
                            <Button className='p-2 mr-1' onClick={() => handleStartEdit(index)}>
                                <LucideEdit className="w-5 h-5 text-white" />
                            </Button>       

                            <Button className='!bg-destructive !dark:bg-darkDestructive p-2' onClick={() => handleRemoveAnswer(index)}>
                                <LucideTrash className="w-5 h-5 text-white" />
                            </Button>       
                        </div>
                    </div>
                ))}  
            </ul>

            {(question.answers?.length < 5 || editState.isEditing) && (
                <>
                    <div>
                        <Textarea
                            placeholder={t('form.exam.answer_placeholder')}
                            value={answer.answer}
                            onChange={(e)=> setAnswer(prev => ({...prev, answer: e.target.value}))}
                            className="resize-none h-[75px] dark:text-white"
                        />
                        {/* <div className='flex items-center gap-2 mt-2'>
                            <Switch
                                id='switch-correct'
                                checked={answer.is_correct}
                                onClick={() => setAnswer(prev => ({...prev, is_correct: !prev.is_correct}))}
                            />
                            <Label htmlFor="switch-correct">{answer.is_correct ? <LucideCircleCheck className="w-5 h-5 text-green-500" /> : <LucideCircleX className="w-5 h-5 text-destructive dark:text-darkDestructive" />}</Label>
                        </div> */}
                    </div>

                    <div>
                        {editState.isEditing ? (
                            <div className='flex items-center gap-2'>
                                <Button type='button' onClick={() => handleEditAnswer(editState.index as number)}>
                                    {t('form.exam.confirm')}
                                </Button>
                                <Button type='button' onClick={handleClear}>
                                    {t('form.exam.cancel')}
                                </Button>
                            </div>
                        ) : (

                            <Button type='button' onClick={handleAddAnswer}>
                                {t('form.exam.add_answer')}
                            </Button>
                        )}
                    </div>
                </>
            )}
        </div>
    )
}

export default AnswersEditor