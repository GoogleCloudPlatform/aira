import { IAnswer, IQuestionEditor } from '@/interfaces/question';
import React, { useEffect, useState } from 'react'
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';

type TAnswerVisorProps = {
    question: IQuestionEditor;
}

const AnswersVisor : React.FC<TAnswerVisorProps> = ({ question }) => {
    const [selectedAnswers, setSelectedAnswers] = useState<IAnswer[]>([])
    const [shuffledAnswers, setShuffledAnswers] = useState<IAnswer[]>([]);

    const correctAnswersArray = question?.answers?.filter( answer => answer.is_correct === true)
    const singleAnswer = correctAnswersArray?.length === 1 ? true : false

    const handleSelectQuestion = (value: any) => {
        const answer = question?.answers?.find( item => item.answer === value)
        if (!answer) return

        if (singleAnswer) {
            setSelectedAnswers([answer])
            return
        }

        const alreadySelected = selectedAnswers.find( item => item.answer === answer.answer)

        if (alreadySelected) {
            const removeSelected = selectedAnswers.filter( item => item.answer !== alreadySelected.answer)
            setSelectedAnswers(removeSelected)
            return
        }

        setSelectedAnswers(prev => ([...prev, answer]))
    }

    useEffect(() => {
        if (question?.answers) {
            const shuffled = [...question.answers].sort(() => Math.random() - 0.5);
            setShuffledAnswers(shuffled);
        }

        return ()=>{
            setSelectedAnswers([])
        }
    }, [question]);

    if (!question.answers) return null

    return (
        <div className='text-white'>
            { !singleAnswer ? (
                <ul className='flex flex-col gap-1'>
                    {shuffledAnswers.map((item, index) => (
                        <li key={index} className='text-black dark:text-white flex items-center gap-6 p-2 bg-gray-100 dark:bg-darkPrimary/20 rounded min-h-10'>
                            <Checkbox checked={selectedAnswers.find(i => i.answer === item.answer) ? true : false} id={`opt-${index}`} onClick={() => handleSelectQuestion(item.answer)}/>
                            <label
                                htmlFor={`opt-${index}`}
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 overflow-hidden break-words h-max"
                            >
                                {item.answer}
                            </label>
                        </li>
                    ))}
                </ul>
            ) : (
                <RadioGroup className='flex flex-col gap-1' onValueChange={(value) => handleSelectQuestion(value)}>
                    {shuffledAnswers.map((item, index) => (
                        <div key={index} className='text-black dark:text-white flex items-center gap-3 p-2 bg-gray-100 dark:bg-darkPrimary/20 rounded min-h-10'>
                            <div className='w-4 h-4'>
                                <RadioGroupItem value={item.answer} id={`opt-${index}`} className='w-4 h-4'/>
                            </div>
                            <Label htmlFor={`opt-${index}`} className='flex-1 overflow-hidden break-words h-max'>{item.answer}</Label>
                        </div>
                    ))}
                </RadioGroup>
            )}
        </div>
    )
}

export default AnswersVisor