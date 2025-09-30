import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getExamResultByUserId } from "@/services/user";

import Scale from "./Scale";
import QuestionsVisor from "../visors/QuestionsVisor";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { SquareArrowOutUpRightIcon } from "lucide-react";
import { ENUM_FLUENT, ENUM_PRE_READER_FOUR, ENUM_PRE_READER_ONE, ENUM_PRE_READER_THREE, ENUM_PRE_READER_TWO, ENUM_READER, QuestionType } from "@/constants/enums";
import { QUESTION_TYPE_COMPLEX_WORDS, QUESTION_TYPE_LOGICAL_SITUATIONS, QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_PHRASES, QUESTION_TYPE_SHORT_EXPLANATIONS, QUESTION_TYPE_UNDERSTANDING_CHECK, QUESTION_TYPE_WORDS } from "@/constants/exams";
import { IExamResponse } from "@/interfaces/exam";
import { IQuestion } from "@/interfaces/question";
import Loading from "../loading/Loading";
import { getResults } from "../answers/AnswersResult";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Progress } from "../ui/progress";

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

    const proficiency = data.questions.find(question => question.type === QuestionType.Words);

    const objectiveQuestions = data.questions.filter(question => question.type === QUESTION_TYPE_MULTIPLE_CHOICE || question.type === QUESTION_TYPE_LOGICAL_SITUATIONS || question.type === QUESTION_TYPE_UNDERSTANDING_CHECK || question.type === QuestionType.IndustryAreas);
    const objectiveQuestionsCount = objectiveQuestions.length;
    const objectiveQuestionsCorrect = objectiveQuestions.filter(question => question.response.ai_is_correct).length;
    const objectiveQuestionsAccuracy = percentCalculation(objectiveQuestionsCorrect, objectiveQuestionsCount);

    const textComprehensionQuestions = data.questions.filter(question => question.type === QUESTION_TYPE_MULTIPLE_CHOICE || question.type === QUESTION_TYPE_UNDERSTANDING_CHECK);
    const textComprehensionQuestionsCount = textComprehensionQuestions.length;
    const textComprehensionQuestionsCorrect = textComprehensionQuestions.filter(question => question.response.ai_is_correct).length;
    const textComprehensionQuestionsAccuracy = percentCalculation(textComprehensionQuestionsCorrect, textComprehensionQuestionsCount);

    const criticalThinkingQuestions = data.questions.filter(question => question.type === QUESTION_TYPE_LOGICAL_SITUATIONS);
    const criticalThinkingQuestionsCount = criticalThinkingQuestions.length;
    const criticalThinkingQuestionsCorrect = criticalThinkingQuestions.filter(question => question.response.ai_is_correct).length;
    const criticalThinkingQuestionsAccuracy = percentCalculation(criticalThinkingQuestionsCorrect, criticalThinkingQuestionsCount);

    const communicationAndProblemSolvingQuestions = data.questions.filter(question => question.type === QUESTION_TYPE_SHORT_EXPLANATIONS);
    const communicationAndProblemSolvingQuestionsCount = communicationAndProblemSolvingQuestions.length;
    const communicationAndProblemSolvingQuestionsCorrect = communicationAndProblemSolvingQuestions.filter(question => question.response.ai_is_correct).length;
    const communicationAndProblemSolvingQuestionsAccuracy = percentCalculation(communicationAndProblemSolvingQuestionsCorrect, communicationAndProblemSolvingQuestionsCount);

    const industryAreaQuestions = data.questions.filter(question => question.type === QuestionType.IndustryAreas);
    const industryAreaQuestionsCount = industryAreaQuestions.length;
    const industryAreaQuestionsCorrect = industryAreaQuestions.filter(question => question.response.ai_is_correct).length;
    const industryAreaQuestionsAccuracy = percentCalculation(industryAreaQuestionsCorrect, industryAreaQuestionsCount);

    const checkResult = (percentual: number) => {
        if (percentual <= 40) return 'low';
        if (percentual <= 65) return 'medium';
        if (percentual <= 100) return 'high';
        return 'low';
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
            return (
                <>
                    <div className="flex flex-col gap-2 ">
                        <b>{t('results.question')}:</b> 
                        {question.data}
                    </div>
                    <div className="flex flex-col gap-1 w-full dark:text-white">
                        <b>{t('results.learner_response')}:</b>
                        <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_LOGICAL_SITUATIONS || question.type === QUESTION_TYPE_UNDERSTANDING_CHECK) {
            return (
                <>                  
                    <div className="flex flex-col gap-2 ">
                        <b>{t('results.question')}:</b> 
                        {question.data}
                    </div>
                    <div className="flex flex-col gap-1 w-full dark:text-white">
                        <div className="my-8 grid space-y-1">
                            <b className="dark:text-white">{t('results.learner_audio')}:</b>
                            <audio controls>
                                <source src={question.response.audio_url} type="audio/wav" />
                                <span>{t('results.no_browser_support')}:</span> 
                            </audio>
                        </div>

                        <b>{t('results.ai_feedback')}:</b>
                        <span>{question.response.ai_feedback}</span>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_SHORT_EXPLANATIONS || question.type === QuestionType.IndustryAreas) {
            return (
                <>
                    <div className="flex flex-col gap-2 ">
                        <b>{t('results.question')}:</b> 
                        {question.data}
                    </div>
                    <div className="flex flex-col gap-1 w-full dark:text-white">
                        <div className="my-8 grid space-y-1">
                            <b className="dark:text-white">{t('results.learner_audio')}:</b>
                            <audio controls>
                                <source src={question.response.audio_url} type="audio/wav" />
                                <span>{t('results.no_browser_support')}:</span> 
                            </audio>
                        </div>

                        <b>{t('results.ai_feedback')}:</b>
                        <span>{question.response.ai_feedback}</span>
                    </div>
                </>
            )
        }

        return (
            <>
                <div className="my-8 grid space-y-1">
                    <b className="text-black dark:text-white">{t('results.learner_audio')}:</b>
                    <audio controls>
                        <source src={question.response.audio_url} type="audio/wav" />
                        <span>{t('results.no_browser_support')}:</span> 
                    </audio>
                </div>
                <div className="grid gap-5">
                    <div className="flex flex-col gap-1 max-h-[400px]">
                        <b className="text-black dark:text-white">{t('results.exam')}:</b>
                        <div className="p-4 overflow-y-auto">
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

        const student_accuracy : number = percentCalculation(rightCount, studentWords);

        const correctAnswersArray = question?.answers?.filter( answer => answer.is_correct === true)
        const singleAnswer = correctAnswersArray?.length === 1 ? true : false
        const userResult = question.response.result
        
        const multipleChoiceResults = ()=>{
            if (question.type !== QUESTION_TYPE_MULTIPLE_CHOICE) return null

            const results = getResults({question, singleAnswer , results: userResult})

            const userRightAnswers = results?.filter( question => question.is_correct === true && question.user_response === true )
            const totalRightAnswers = results?.filter( question => question.is_correct === true)

            const userWrongAnswers = results?.filter(question => question.is_correct === false && question.user_response === true);

            if (userRightAnswers?.length === totalRightAnswers?.length && userWrongAnswers?.length === 0) {
                return true;
            }

            return false
        }

        return (
            <div 
                className={`border border-border dark:border-darkBorder rounded-md p-2 sm:p-5 shadow-md bg-white dark:bg-white/10 dark:hover:bg-white/5 transition-all`}
            >
                <div className="flex flex-col justify-between items-center">
                    <div className="header w-full flex h-fit items-center justify-between mb-6 text-black dark:text-white">
                        <div className="text-xl flex gap-1 text-black dark:text-white">
                            <b>{t(`text-editor.editor.${question.type}`)}</b>
                        </div>
                        <Dialog>
                            <DialogTrigger title={t('results.buttons.show_results')}>
                                <SquareArrowOutUpRightIcon />
                            </DialogTrigger>
                            <DialogContent
                                className={`${question.type === 'phrases' && 'md:min-w-[90%] text-black dark:text-white'}} min-w-[90%] max-w-[90%] lg:max-w-[1024px] dark:bg-darkBackground dark:border-darkBorder`}
                            >
                                <DialogHeader>
                                    <DialogTitle className="text-black dark:text-white">{t(`text-editor.editor.${question.type}`)}</DialogTitle>
                                </DialogHeader>

                                {renderAnswer(question)}
                            </DialogContent>
                        </Dialog>
                    </div>

                    {question.type === QUESTION_TYPE_MULTIPLE_CHOICE && (
                        <div className="flex flex-col gap-2 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 ">
                                <b>{t('results.question')}:</b> 
                                {question.data}
                            </div>
                            <div className="flex gap-2 ">
                                <b>{t('results.learner_response')}:</b> 
                                <span>{multipleChoiceResults() ? t('results.true') : t('results.false')}</span>
                            </div>
                        </div>
                    )}

                    {(QUESTION_TYPE_WORDS === question.type || QUESTION_TYPE_COMPLEX_WORDS === question.type || QUESTION_TYPE_PHRASES === question.type) && (
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
                    
                    {(QUESTION_TYPE_LOGICAL_SITUATIONS === question.type || QUESTION_TYPE_UNDERSTANDING_CHECK === question.type) && (
                        <div className="flex flex-col gap-2 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 ">
                                <b>{t('results.question')}:</b> 
                                {question.data}
                            </div>
                            <div className="flex gap-2 ">
                                <b>{t('results.learner_response')}:</b> 
                                <span>{question.response.ai_is_correct ? t('results.true') : t('results.false')}</span>
                            </div>
                        </div>
                    )}
                    
                    {(QUESTION_TYPE_SHORT_EXPLANATIONS === question.type || QuestionType.IndustryAreas === question.type) && (
                        <div className="flex flex-col gap-2 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 ">
                                <b>{t('results.question')}:</b> 
                                {question.data}
                                <div className="flex gap-2 ">
                                    <b>{t('results.learner_response')}:</b> 
                                    <span>{question.response.ai_is_correct ? t('results.true') : t('results.false')}</span>
                                </div>                            
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="w-full">
            <div className="flex flex-col md:flex-row items-stretch justify-center gap-4 h-max mb-10">
                <fieldset className="border-2 border-slate-100 dark:border-slate-900 rounded-lg p-2 flex-1 flex flex-col gap-4 items-center justify-center text-black dark:text-white">
                    <legend className="px-1 font-bold">{t('results.general_performance')}</legend>
                    {objectiveQuestionsCount > 0 ? (
                        <>
                            <p className="text-center text-[50px] font-bold">{objectiveQuestionsAccuracy.toFixed(0)}%</p>
                            <Progress value={objectiveQuestionsAccuracy} className="h-6 rounded-none" />
                            <p>{t('results.general_performance_description', { accuracy: objectiveQuestionsAccuracy.toFixed(0) })}</p>
                        </>
                    ) : (
                        <p className="text-left break-words w-full pl-1">{t('results.no_objective_questions')}</p>
                    )}
                </fieldset>

                <fieldset className="border-2 border-slate-100 dark:border-slate-900 rounded-lg p-2 flex-1 text-black dark:text-white">
                    <legend className="px-1 font-bold">{t('results.general_feedback')}</legend>
                    <p className="text-justify break-words w-full pl-1">{data.ai_exam_feedback || t('results.no_ai_feedback')}</p>
                </fieldset>
            </div>

            <Tabs defaultValue={`${proficiency ? 'lecture_proficiency' : textComprehensionQuestionsCount > 0 ? 'text_compreension' : criticalThinkingQuestionsCount > 0 ? 'critical_thinking' : communicationAndProblemSolvingQuestionsCount > 0 ? 'communication_and_problem_solving' : industryAreaQuestionsCount > 0 ? 'industry_areas' : ''}`} className="w-full">
                <TabsList className="bg-slate-100 dark:bg-slate-900 rounded-lg p-1 w-full justify-start">
                    {proficiency ? (
                        <TabsTrigger value="lecture_proficiency" className="w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.lecture_proficiency')}</span>
                        </TabsTrigger>
                    ) : null}

                    {textComprehensionQuestionsCount ? (
                        <TabsTrigger value="text_compreension" className="w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.text_compreension')}</span>
                        </TabsTrigger>
                    ) : null}

                    {criticalThinkingQuestionsCount ? (
                        <TabsTrigger value="critical_thinking" className="w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.critical_thinking')}</span>
                        </TabsTrigger>
                    ) : null}

                    {communicationAndProblemSolvingQuestionsCount ? (
                        <TabsTrigger value="communication_and_problem_solving" className="w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.communication_and_problem_solving')}</span>
                        </TabsTrigger>
                    ) : null}

                    {industryAreaQuestionsCount ? (
                        <TabsTrigger value="industry_areas" className="w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.industry_areas')}</span>
                        </TabsTrigger>
                    ) : null}
                </TabsList>

                <TabsContent value="lecture_proficiency" className="w-full p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <div className="mt-10 mb-20">
                        <Scale 
                            selectedValue={data.questions[0].response.user_rating} 
                            options={[ ENUM_PRE_READER_ONE, ENUM_PRE_READER_TWO, ENUM_PRE_READER_THREE, ENUM_PRE_READER_FOUR, ENUM_READER, ENUM_FLUENT]} 
                            classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
                        />
                    </div>

                    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-2">
                        {data?.questions?.map((question, index) => {
                            if (QUESTION_TYPE_WORDS === question.type || QUESTION_TYPE_COMPLEX_WORDS === question.type || QUESTION_TYPE_PHRASES === question.type) {
                                return (
                                    <div key={index} >
                                        {renderQuestion(question)}
                                    </div>
                                )
                            }
                        })}
                    </div>
                </TabsContent>

                <TabsContent value="text_compreension" className="w-full p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <div className="mt-10 mb-20">
                        <Scale 
                            selectedValue={checkResult(textComprehensionQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
                        />
                    </div>
                    
                    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-2">
                        {data?.questions?.map((question, index) => {
                            if (QUESTION_TYPE_MULTIPLE_CHOICE === question.type || QUESTION_TYPE_UNDERSTANDING_CHECK === question.type) {
                                return (
                                    <div key={index} >
                                        {renderQuestion(question)}
                                    </div>
                                )
                            }
                        })}
                    </div>
                </TabsContent>

                <TabsContent value="critical_thinking" className="w-full p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <div className="mt-10 mb-20">
                        <Scale 
                            selectedValue={checkResult(criticalThinkingQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
                        />
                    </div>
                    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-2">
                        {data?.questions?.map((question, index) => {
                            if (QUESTION_TYPE_LOGICAL_SITUATIONS === question.type) {
                                return (
                                    <div key={index} >
                                        {renderQuestion(question)}
                                    </div>
                                )
                            }
                        })}
                    </div>
                </TabsContent>

                <TabsContent value="communication_and_problem_solving" className="w-full p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <div className="mt-10 mb-20">
                        <Scale 
                            selectedValue={checkResult(communicationAndProblemSolvingQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
                        />
                    </div>
                    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-2">
                        {data?.questions?.map((question, index) => {
                            if (QUESTION_TYPE_SHORT_EXPLANATIONS === question.type) {
                                return (
                                    <div key={index} >
                                        {renderQuestion(question)}
                                    </div>
                                )
                            }
                        })}
                    </div>
                </TabsContent>

                <TabsContent value="industry_areas" className="w-full p-4 bg-slate-100 dark:bg-slate-900 rounded-lg">
                    <div className="mt-10 mb-20">
                        <Scale 
                            selectedValue={checkResult(industryAreaQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-700 sm:via-yellow-300 sm:to-green-600 rounded-md sm:divide-x-2 sm:divide-white dark:sm:divide-gray-900"
                        />
                    </div>
                    <div className="flex flex-col gap-4 lg:grid lg:grid-cols-2">
                        {data?.questions?.map((question, index) => {
                            if (QuestionType.IndustryAreas === question.type) {
                                return (
                                    <div key={index} >
                                        {renderQuestion(question)}
                                    </div>
                                )
                            }
                        })}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}

export default ExamResult