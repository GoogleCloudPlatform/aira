import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getExamResultByUserId } from "@/services/user";

import Scale from "./Scale";
import QuestionsVisor from "../visors/QuestionsVisor";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { SquareArrowOutUpRightIcon } from "lucide-react";
import { ENUM_FLUENT, ENUM_NO_RATING, ENUM_PRE_READER_FOUR, ENUM_PRE_READER_ONE, ENUM_PRE_READER_THREE, ENUM_PRE_READER_TWO, ENUM_READER } from "@/constants/enums";
import { QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_PHRASES } from "@/constants/exams";
import { IExamResponse } from "@/interfaces/exam";
import { IQuestion } from "@/interfaces/question";
import { isEmpty } from "lodash";
import Loading from "../loading/Loading";
import { getResults } from "../answers/AnswersResult";

type TExamResult = {
    exam_id: string;
    user_id: string;
}

const ExamResult : React.FC<TExamResult> = ({ exam_id, user_id }) => {
    const [mounted, setMounted] = useState<boolean>(false);

    const queryClient = useQueryClient();
    const t = useTranslations('');

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: ['exam_result'] });
        }
    }, [mounted, queryClient]);
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, [mounted]);
    
    const { data, isLoading } = useQuery<IExamResponse>({ 
        queryKey: ['exam_result', exam_id, user_id], 
        queryFn: () => getExamResultByUserId(exam_id, user_id), 
        retryOnMount: false, retry: false,
        enabled: mounted
    });
    
    const percentCalculation = (score: number, total: number) => {
        if (total === 0) {
            return 0; // To avoid division by zero if there are no words
        }
        
        const percentage = (score / total) * 100;
        return percentage;
    }
    
    if (!mounted || !data || !exam_id || !user_id) return 
    if (isLoading) return <Loading style="vertical" text={true}/>;
    
    const renderStatus = () => {
        if (!data.questions || isEmpty(data.questions) || !data.questions[0]) return null;

        const user_rating = data.questions[0].response.user_rating;

        if (user_rating) return (
            <Scale 
                selectedValue={user_rating} 
                options={[ ENUM_PRE_READER_ONE, ENUM_PRE_READER_TWO, ENUM_PRE_READER_THREE, ENUM_PRE_READER_FOUR, ENUM_READER, ENUM_FLUENT]} 
                classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
            />
        );

        return null        
    }

    const renderAnswer = (question: IQuestion) => {
        if (question.type === QUESTION_TYPE_PHRASES) {
            return (
                <>
                    <div className="my-8 grid space-y-1 w-full dark:text-white">
                        <b>{t('results.learner_audio')}:</b>
                        <audio controls>
                            <source src={question.response.audio_url} type="audio/wav" />
                            <span className="text-black dark:text-white">{t('results.no_browser_support')}:</span> 
                        </audio>
                    </div>
                    <div className="grid grid-cols-2 gap-5 w-full">
                        <div className="flex flex-col gap-1 w-full dark:text-white">
                            <b>{t('results.exam')}:</b>
                            <QuestionsVisor question={question} userResult={true}/>
                        </div>
                        <div className="flex flex-col gap-1 w-full dark:text-white">
                            <b>{t('results.learner_response')}:</b>
                            <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                        </div>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_MULTIPLE_CHOICE) {
            // console.log(question)
            // console.log(question.response)
            return (
                <>
                    <div className="flex flex-col gap-1 w-full dark:text-white">
                        <b>{t('results.learner_response')}:</b>
                        <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                    </div>
                </>
            )
        } 

        return (
            <>
                <div className="my-8 grid space-y-1">
                    <b className="dark:text-white">{t('results.learner_audio')}:</b>
                    <audio controls>
                        <source src={question.response.audio_url} type="audio/wav" />
                        <span>{t('results.no_browser_support')}:</span> 
                    </audio>
                </div>
                <div className="grid gap-5">
                    <div className="flex flex-col gap-1 max-h-[400px]">
                        <b className="dark:text-white">{t('results.exam')}:</b>
                        <div className="p-4 overflow-y-auto ">
                            <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                        </div>
                    </div>
                </div>
            </>
        ) 
    }

    const renderQuestion = (question: IQuestion) => {
        const { response } = question;

        const totalWords = question.data.split(" ").length;
        const rightCount = response.right_count;
        const studentWords = response.result.length;

        // const total_accuracy : number = percentCalculation(rightCount, totalWords);
        const student_accuracy : number = percentCalculation(rightCount, studentWords);

        const correctAnswersArray = question?.answers?.filter( answer => answer.is_correct === true)
        const singleAnswer = correctAnswersArray?.length === 1 ? true : false
        const userResult = question.response.result
        
        const multipleChocieResults = ()=>{
            if (question.type !== QUESTION_TYPE_MULTIPLE_CHOICE) return null

            const results = getResults({question, singleAnswer , results: userResult})

            const userRightAnswers = results?.map( question => question.is_correct === true && question.user_response === true )
            const totalRightAnswers = results?.filter( question => question.is_correct === true)

            const userWrongAnswers = results?.filter(question => question.is_correct === false && question.user_response === true);

            if (userRightAnswers?.length === totalRightAnswers?.length && userWrongAnswers?.length === 0) {
                return true;
            }

            return false
        }

        return (
            <div 
                className={`border border-border dark:border-darkBorder rounded-md p-2 sm:p-5 shadow-md bg-black/5 dark:bg-white/10 dark:hover:bg-white/5 transition-all`}
            >
                <div className="flex flex-col justify-between items-center">
                    <div className="header w-full flex h-fit items-center justify-between mb-6 text-black dark:text-white">
                        <div className="text-xl flex gap-1 ">
                            <b>{t(`text-editor.editor.${question.type}`)}</b>
                        </div>
                        <Dialog>
                            <DialogTrigger title={t('results.buttons.show_results')}>
                                <SquareArrowOutUpRightIcon />
                            </DialogTrigger>
                            <DialogContent
                                className={`${question.type === 'phrases' && 'md:min-w-[90%] text-white'}} min-w-[90%] max-w-[90%] lg:max-w-[1024px] dark:bg-darkBackground dark:border-darkBorder`}
                            >
                                <DialogHeader>
                                    <DialogTitle className="text-black dark:text-white">{t(`text-editor.editor.${question.type}`)}</DialogTitle>
                                </DialogHeader>

                                {renderAnswer(question)}
                            </DialogContent>
                        </Dialog>
                    </div>
                    {QUESTION_TYPE_MULTIPLE_CHOICE === question.type ? (
                        <div className="flex flex-col gap-2 w-full text-black dark:text-white">
                            <div className="flex gap-2 ">
                                <span>{t('results.learner_response')}:</span> 
                                <b>{multipleChocieResults() ? t('results.true') : t('results.false')}</b>
                            </div>
                        </div>
                    ):(
                        <div className="flex flex-col gap-2 w-full text-black dark:text-white">
                            <div className="flex gap-2 ">
                                <span>{t('results.item_word_total')}:</span> 
                                <b>{totalWords}</b>
                            </div>
                            <div className="flex gap-2 ">
                                <span>{t('results.words_read_total')}:</span> 
                                <b>{studentWords}</b>
                            </div>
                            <div className="flex gap-2 ">
                                <span>{t('results.correctly_read_total')}:</span> 
                                <b>{rightCount}</b>
                            </div>
                            {question.type === 'phrases' && (
                                <div className="flex gap-2 ">
                                    <span>{t('results.total_accuracy')}:</span> 
                                    <b>{rightCount}/{studentWords} ({student_accuracy.toFixed(2)}%)</b>
                                </div>
                            ) }
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="mb-5 sm:mt-10 sm:mb-20 md:block">{renderStatus()}</div>

            <div className="flex flex-col gap-4">
                {data?.questions?.map((question, index) => (
                    <div key={index} >
                        {renderQuestion(question)}
                    </div>
                ))}
            </div>
        </>
    )
}

export default ExamResult