import React from 'react'
import { IQuestionEditor } from '@/interfaces/question';
import { Label } from '../ui/label';
import { Check, X } from 'lucide-react';

type TAnswersResultProps = {
    question: IQuestionEditor;
    results?: string[]
}

export const getResults = ({question, singleAnswer, results} : { question : IQuestionEditor, singleAnswer: boolean, results: string[]}) => {
    if (singleAnswer) {
        const result = question.answers?.map( answer => {
            if (answer.answer === results[0]) {
                if (answer.is_correct) {
                    return {
                        ...answer,
                        user_response: true,
                        background: 'text-white bg-green-600'
                    }
                } else {
                    return {
                        ...answer,
                        user_response: true,
                        background: 'text-white bg-destructive dark:bg-darkDestructive'
                    }
                }
            }

            if (answer.is_correct) {
                return {
                    ...answer,
                    user_response: false,
                    background: 'bg-gray-100 dark:bg-darkPrimary/20'
                }
            } else {
                return {
                    ...answer,
                    user_response: false,
                    background: 'bg-gray-100 dark:bg-darkPrimary/20'
                }
            }
        })
        
        return result
    } else {
        const result = question.answers?.map( answer => {
            const userResponse = results.find(user_answer => user_answer === answer.answer)
            if (userResponse) {
                if (answer.is_correct) {
                    return {
                        ...answer,
                        user_response: true,
                        background: 'text-white bg-green-600'
                    }
                } else {
                    return {
                        ...answer,
                        user_response: true,
                        background: 'text-white bg-destructive dark:bg-darkDestructive'
                    }
                }
            }

            if (answer.is_correct) {
                return {
                    ...answer,
                    user_response: false,
                    background: 'bg-gray-100 dark:bg-darkPrimary/20'
                }
            } else {
                return {
                    ...answer,
                    user_response: false,
                    background: 'bg-gray-100 dark:bg-darkPrimary/20'
                }
            }
        })
        
        return result
    }

}

const AnswersResult : React.FC<TAnswersResultProps> = ({ question, results }) => {
    if (!question.answers) return null
    if (!results) return null
    
    const correctAnswersArray = question?.answers?.filter( answer => answer.is_correct === true)
    const singleAnswer = correctAnswersArray?.length === 1 ? true : false

    const questionResults = getResults({question, singleAnswer , results})

    return (
        <div className='text-white'>
            { !singleAnswer ? (
                <ul className='flex flex-col gap-1'>
                    {questionResults?.map((item, index) => (
                        <li key={index} className={`text-black dark:text-white flex items-center gap-3 p-2 ${item.background} rounded min-h-10`}>
                            {item.is_correct === true && item.user_response === true ? (
                                <Check />
                            ) : item.is_correct === false && item.user_response === true ? (
                                <Check />
                            ) : item.is_correct === true ? (
                                <X />
                            ): null}
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
                <ul className='flex flex-col gap-1'>
                    {questionResults?.map((item, index) => (
                        <div key={index} className={`text-black dark:text-white flex items-center gap-3 p-2 ${item.background} rounded min-h-10`}>
                            {item.is_correct === true && item.user_response === true ? (
                                <Check />
                            ) : item.is_correct === false && item.user_response === true ? (
                                <Check />
                            ) : item.is_correct === true ? (
                                <X />
                            ): null}
                            <Label htmlFor={`opt-${index}`} className='flex-1 overflow-hidden break-words h-max'>{item.answer}</Label>
                        </div>
                    ))}
                </ul>
            )
            }
        </div>
    )
}

export default AnswersResult