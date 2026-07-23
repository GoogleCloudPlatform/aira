import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getExamResultByUserId } from "@/services/user";

import Scale from "./Scale";
import QuestionsVisor from "../visors/QuestionsVisor";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { SquareArrowOutUpRightIcon, SparklesIcon, TrophyIcon, ClipboardListIcon, ArrowUpRightIcon, BookOpenIcon, CheckCircle2Icon, ActivityIcon } from "lucide-react";
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
            return 0;
        }
        
        const percentage = (score / total) * 100;
        return percentage;
    }
    
    if (!mounted) return null;
    if (isLoading) return <Loading style="vertical" text={true}/>;
    if (!data || !exam_id || !user_id) return null;

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
                        <b className="text-slate-700 dark:text-slate-300">{t('results.learner_audio')}:</b>
                        <audio controls className="w-full max-w-md mt-1">
                            <source src={question.response.audio_url} type="audio/wav" />
                            <span className="text-black dark:text-white">{t('results.no_browser_support')}:</span> 
                        </audio>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
                        <div className="flex flex-col gap-2 w-full dark:text-white bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.exam')}:</b>
                            <QuestionsVisor question={question} userResult={true}/>
                        </div>
                        <div className="flex flex-col gap-2 w-full dark:text-white bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.learner_response')}:</b>
                            <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                        </div>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_MULTIPLE_CHOICE) {
            return (
                <>
                    <div className="flex flex-col gap-2 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                        <b className="text-slate-800 dark:text-slate-200">{t('results.question')}:</b> 
                        <span className="text-slate-600 dark:text-slate-300">{question.data}</span>
                    </div>
                    <div className="flex flex-col gap-2 w-full mt-4 dark:text-white bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                        <b className="text-slate-800 dark:text-slate-200">{t('results.learner_response')}:</b>
                        <QuestionsVisor question={question} userResult={true} results={question.response.result}/>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_LOGICAL_SITUATIONS || question.type === QUESTION_TYPE_UNDERSTANDING_CHECK) {
            return (
                <>                  
                    <div className="flex flex-col gap-2 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                        <b className="text-slate-800 dark:text-slate-200">{t('results.question')}:</b> 
                        <span className="text-slate-600 dark:text-slate-300">{question.data}</span>
                    </div>
                    <div className="flex flex-col gap-2 w-full mt-4 dark:text-white">
                        <div className="my-4 grid space-y-1 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.learner_audio')}:</b>
                            <audio controls className="w-full max-w-md mt-1">
                                <source src={question.response.audio_url} type="audio/wav" />
                                <span>{t('results.no_browser_support')}:</span> 
                            </audio>
                        </div>

                        <div className="bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.ai_feedback')}:</b>
                            <span className="block mt-2 leading-relaxed text-slate-600 dark:text-slate-300">{question.response.ai_feedback}</span>
                        </div>
                    </div>
                </>
            )
        } 

        if (question.type === QUESTION_TYPE_SHORT_EXPLANATIONS || question.type === QuestionType.IndustryAreas) {
            return (
                <>
                    <div className="flex flex-col gap-2 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                        <b className="text-slate-800 dark:text-slate-200">{t('results.question')}:</b> 
                        <span className="text-slate-600 dark:text-slate-300">{question.data}</span>
                    </div>
                    <div className="flex flex-col gap-2 w-full mt-4 dark:text-white">
                        <div className="my-4 grid space-y-1 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.learner_audio')}:</b>
                            <audio controls className="w-full max-w-md mt-1">
                                <source src={question.response.audio_url} type="audio/wav" />
                                <span>{t('results.no_browser_support')}:</span> 
                            </audio>
                        </div>

                        <div className="bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                            <b className="text-slate-800 dark:text-slate-200">{t('results.ai_feedback')}:</b>
                            <span className="block mt-2 leading-relaxed text-slate-600 dark:text-slate-300">{question.response.ai_feedback}</span>
                        </div>
                    </div>
                </>
            )
        }

        return (
            <>
                <div className="my-4 grid space-y-1 bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                    <b className="text-slate-850 dark:text-slate-200">{t('results.learner_audio')}:</b>
                    <audio controls className="w-full max-w-md mt-1">
                        <source src={question.response.audio_url} type="audio/wav" />
                        <span>{t('results.no_browser_support')}:</span> 
                    </audio>
                </div>
                <div className="grid gap-5 mt-4">
                    <div className="flex flex-col gap-1 max-h-[400px] bg-slate-50/50 dark:bg-slate-950/40 p-4 rounded-xl border border-slate-100/80 dark:border-slate-900/50">
                        <b className="text-slate-850 dark:text-slate-200">{t('results.exam')}:</b>
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
                className={`border border-slate-100 dark:border-slate-900 rounded-2xl p-5 shadow-sm bg-white/70 backdrop-blur-sm dark:bg-white/5 dark:hover:bg-white/10 transition-all duration-300 hover:shadow-md hover:-translate-y-0.5`}
            >
                <div className="flex flex-col justify-between items-center">
                    <div className="header w-full flex h-fit items-center justify-between mb-6 text-black dark:text-white">
                        <div className="flex items-center gap-2">
                            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 rounded-xl">
                                <BookOpenIcon className="h-5 w-5" />
                            </div>
                            <b className="text-lg font-bold text-slate-800 dark:text-slate-100">{t(`text-editor.editor.${question.type}`)}</b>
                        </div>
                        <Dialog>
                            <DialogTrigger asChild>
                                <button className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded-xl transition-all duration-200 shadow-sm hover:shadow border border-transparent hover:border-indigo-100 dark:hover:border-indigo-900/50">
                                    <SquareArrowOutUpRightIcon className="h-5 w-5" />
                                </button>
                            </DialogTrigger>
                            <DialogContent
                                className={`${question.type === 'phrases' && 'md:min-w-[90%] text-black dark:text-white'} min-w-[90%] max-w-[90%] lg:max-w-[1024px] dark:bg-darkBackground dark:border-darkBorder`}
                            >
                                <DialogHeader>
                                    <DialogTitle className="text-black dark:text-white flex items-center gap-2">
                                        <BookOpenIcon className="h-5 w-5 text-indigo-600" />
                                        {t(`text-editor.editor.${question.type}`)}
                                    </DialogTitle>
                                </DialogHeader>

                                {renderAnswer(question)}
                            </DialogContent>
                        </Dialog>
                    </div>

                    {question.type === QUESTION_TYPE_MULTIPLE_CHOICE && (
                        <div className="flex flex-col gap-4 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 bg-slate-50/40 dark:bg-slate-950/30 p-3.5 rounded-xl border border-slate-100/50 dark:border-slate-900/50">
                                <b className="text-slate-700 dark:text-slate-300">{t('results.question')}:</b> 
                                <span className="text-slate-600 dark:text-slate-400 leading-relaxed">{question.data}</span>
                            </div>
                            <div className="flex items-center justify-between py-2 px-4 bg-indigo-50/40 dark:bg-indigo-950/20 rounded-xl border border-indigo-100/30 dark:border-indigo-900/20">
                                <span className="text-slate-700 dark:text-slate-300 font-bold">{t('results.learner_response')}:</span> 
                                <span className={`text-sm font-extrabold px-3 py-1 rounded-full ${multipleChoiceResults() ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400'}`}>
                                    {multipleChoiceResults() ? t('results.true') : t('results.false')}
                                </span>
                            </div>
                        </div>
                    )}

                    {(QUESTION_TYPE_WORDS === question.type || QUESTION_TYPE_COMPLEX_WORDS === question.type || QUESTION_TYPE_PHRASES === question.type) && (
                        <div className="flex flex-col gap-4 w-full text-black dark:text-white">
                            {/* Stats Grid */}
                            <div className="grid grid-cols-3 gap-2">
                                <div className="flex flex-col items-center justify-center p-3 bg-slate-50/50 dark:bg-slate-900/40 rounded-xl border border-slate-100/60 dark:border-slate-900/50 text-center">
                                    <span className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold mb-1">{t('results.item_word_total')}</span>
                                    <span className="text-lg font-extrabold text-slate-700 dark:text-slate-200">{totalWords}</span>
                                </div>
                                <div className="flex flex-col items-center justify-center p-3 bg-indigo-50/30 dark:bg-indigo-950/20 rounded-xl border border-indigo-100/20 dark:border-indigo-900/20 text-center">
                                    <span className="text-[10px] uppercase tracking-wider text-indigo-400 font-bold mb-1">{t('results.words_read_total')}</span>
                                    <span className="text-lg font-extrabold text-indigo-700 dark:text-indigo-300">{studentWords}</span>
                                </div>
                                <div className="flex flex-col items-center justify-center p-3 bg-emerald-50/30 dark:bg-emerald-950/20 rounded-xl border border-emerald-100/20 dark:border-emerald-900/20 text-center">
                                    <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold mb-1">{t('results.correctly_read_total')}</span>
                                    <span className="text-lg font-extrabold text-emerald-700 dark:text-emerald-300">{rightCount}</span>
                                </div>
                            </div>

                            {/* Precision Progress Bar */}
                            <div className="flex flex-col gap-1.5 mt-2">
                                <div className="flex justify-between text-xs font-bold text-slate-500 dark:text-slate-400">
                                    <span>Precisão de Leitura:</span>
                                    <span className="text-indigo-600 dark:text-indigo-400">{student_accuracy.toFixed(1)}%</span>
                                </div>
                                <Progress value={student_accuracy} className="h-2 bg-slate-100 dark:bg-slate-900" />
                            </div>
                        </div>
                    )}
                    
                    {(QUESTION_TYPE_LOGICAL_SITUATIONS === question.type || QUESTION_TYPE_UNDERSTANDING_CHECK === question.type) && (
                        <div className="flex flex-col gap-4 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 bg-slate-50/40 dark:bg-slate-950/30 p-3.5 rounded-xl border border-slate-100/50 dark:border-slate-900/50">
                                <b className="text-slate-700 dark:text-slate-300">{t('results.question')}:</b> 
                                <span className="text-slate-600 dark:text-slate-400 leading-relaxed">{question.data}</span>
                            </div>
                            <div className="flex items-center justify-between py-2 px-4 bg-indigo-50/40 dark:bg-indigo-950/20 rounded-xl border border-indigo-100/30 dark:border-indigo-900/20">
                                <span className="text-slate-700 dark:text-slate-300 font-bold">{t('results.learner_response')}:</span> 
                                <span className={`text-sm font-extrabold px-3 py-1 rounded-full ${question.response.ai_is_correct ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400'}`}>
                                    {question.response.ai_is_correct ? t('results.true') : t('results.false')}
                                </span>
                            </div>
                        </div>
                    )}
                    
                    {(QUESTION_TYPE_SHORT_EXPLANATIONS === question.type || QuestionType.IndustryAreas === question.type) && (
                        <div className="flex flex-col gap-4 w-full text-black dark:text-white">
                            <div className="flex flex-col gap-2 bg-slate-50/40 dark:bg-slate-950/30 p-3.5 rounded-xl border border-slate-100/50 dark:border-slate-900/50">
                                <b className="text-slate-700 dark:text-slate-300">{t('results.question')}:</b> 
                                <span className="text-slate-600 dark:text-slate-400 leading-relaxed">{question.data}</span>
                            </div>
                            <div className="flex items-center justify-between py-2 px-4 bg-indigo-50/40 dark:bg-indigo-950/20 rounded-xl border border-indigo-100/30 dark:border-indigo-900/20">
                                <span className="text-slate-700 dark:text-slate-300 font-bold">{t('results.learner_response')}:</span> 
                                <span className={`text-sm font-extrabold px-3 py-1 rounded-full ${question.response.ai_is_correct ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400'}`}>
                                    {question.response.ai_is_correct ? t('results.true') : t('results.false')}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    const renderMarkdown = (text: string) => {
        if (!text) return null;
        const lines = text.split("\n");
        return lines.map((line, index) => {
            const trimmedLine = line.trim();
            const isBullet = trimmedLine.startsWith("-") || (trimmedLine.startsWith("*") && !trimmedLine.startsWith("**"));
            const isSubBullet = line.startsWith(" ") || line.startsWith("\t");
            const cleanLine = isBullet ? trimmedLine.substring(1).trim() : line;
            
            const parts = cleanLine.split(/\*\*(.*?)\*\*/g);
            const content = parts.map((part, partIndex) => {
                if (partIndex % 2 === 1) {
                    return <strong key={partIndex} className="font-extrabold text-slate-800 dark:text-white">{part}</strong>;
                }
                return part;
            });
            
            if (isBullet) {
                return (
                    <li 
                        key={index} 
                        className={`list-disc mb-1.5 text-slate-600 dark:text-slate-300 text-sm leading-relaxed ${isSubBullet ? 'ml-9 opacity-90' : 'ml-5'}`}
                    >
                        {content}
                    </li>
                );
            }
            if (line.trim() === "") {
                return <div key={index} className="h-2.5" />;
            }
            return (
                <p key={index} className="mb-2 text-slate-600 dark:text-slate-300 text-sm leading-relaxed text-justify break-words w-full">
                    {content}
                </p>
            );
        });
    };

    return (
        <div className="w-full">
            {/* Performance & AI Insights grid */}
            <div className="flex flex-col md:flex-row items-stretch justify-center gap-5 h-max mb-8">
                {/* Left Card (Performance Card) */}
                <div className="flex-1 flex flex-col items-center justify-center p-6 rounded-3xl border border-slate-100 dark:border-slate-900 bg-white/70 dark:bg-white/5 backdrop-blur-sm shadow-sm shadow-slate-50 dark:shadow-none">
                    <div className="flex items-center gap-2 self-start mb-4">
                        <div className="p-1.5 bg-amber-50 dark:bg-amber-950/30 text-amber-500 dark:text-amber-400 rounded-lg">
                            <TrophyIcon className="h-4.5 w-4.5" />
                        </div>
                        <span className="text-sm font-extrabold text-slate-400 dark:text-slate-500 uppercase tracking-wide">{t('results.general_performance')}</span>
                    </div>

                    {objectiveQuestionsCount > 0 ? (
                        <div className="flex flex-col items-center w-full mt-2">
                            <span className="text-5xl font-extrabold text-slate-800 dark:text-slate-100 tracking-tight mb-3">{objectiveQuestionsAccuracy.toFixed(0)}%</span>
                            <Progress value={objectiveQuestionsAccuracy} className="h-2 bg-slate-100 dark:bg-slate-900 w-full max-w-xs mb-4" />
                            <p className="text-center text-sm text-slate-500 dark:text-slate-400 leading-relaxed max-w-xs">{t('results.general_performance_description', { accuracy: objectiveQuestionsAccuracy.toFixed(0) })}</p>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-4 text-slate-450 text-center w-full">
                            <ClipboardListIcon className="h-8 w-8 mb-2 opacity-40" />
                            <p className="text-sm leading-relaxed text-slate-400 dark:text-slate-500 max-w-xs">{t('results.no_objective_questions')}</p>
                        </div>
                    )}
                </div>

                {/* Right Card (Gemini AI Feedback Card) */}
                <div className="flex-1 flex flex-col p-6 rounded-3xl border border-indigo-100/80 dark:border-indigo-950 bg-gradient-to-br from-indigo-50/30 to-white dark:from-indigo-950/10 dark:to-slate-950/40 shadow-sm shadow-indigo-50/20 dark:shadow-none relative overflow-hidden">
                    <div className="absolute -right-8 -top-8 w-28 h-28 bg-indigo-300/10 dark:bg-indigo-600/5 rounded-full blur-2xl"></div>
                    
                    <div className="flex items-center justify-between mb-4 z-10">
                        <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-indigo-600 text-white rounded-lg animate-pulse">
                                <SparklesIcon className="h-4.5 w-4.5" />
                            </div>
                            <span className="text-sm font-extrabold text-indigo-700 dark:text-indigo-400 uppercase tracking-wide">{t('results.general_feedback')}</span>
                        </div>
                        <span className="text-[10px] font-extrabold tracking-wide uppercase px-2 py-0.5 bg-indigo-100/80 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300 rounded-full">Gemini Insights</span>
                    </div>
                    
                    <div className="flex-1 flex flex-col items-start z-10 w-full">
                        {renderMarkdown(data.ai_exam_feedback || t('results.no_ai_feedback'))}
                    </div>
                </div>
            </div>

            <div className="bg-white/40 dark:bg-white/5 p-6 rounded-3xl border border-slate-100/80 dark:border-slate-900/50 backdrop-blur-sm mt-12 mb-8 shadow-sm">
                <Scale 
                    selectedValue={data.questions[0].response.user_rating} 
                    options={[ ENUM_PRE_READER_ONE, ENUM_PRE_READER_TWO, ENUM_PRE_READER_THREE, ENUM_PRE_READER_FOUR, ENUM_READER, ENUM_FLUENT]} 
                    classes="sm:bg-gradient-to-r sm:from-red-500 sm:via-yellow-400 sm:to-emerald-500 sm:divide-x-2 sm:divide-white dark:sm:divide-slate-900"
                />
            </div>

            <Tabs defaultValue={`${proficiency ? 'lecture_proficiency' : textComprehensionQuestionsCount > 0 ? 'text_compreension' : criticalThinkingQuestionsCount > 0 ? 'critical_thinking' : communicationAndProblemSolvingQuestionsCount > 0 ? 'communication_and_problem_solving' : industryAreaQuestionsCount > 0 ? 'specific_knowledge' : ''}`} className="w-full">
                <TabsList className="bg-slate-50 dark:bg-slate-950/80 border border-slate-100 dark:border-slate-900 text-slate-600 dark:text-slate-400 rounded-2xl p-1.5 w-full justify-start gap-1 h-auto mb-6">
                    {proficiency ? (
                        <TabsTrigger value="lecture_proficiency" className="rounded-xl py-2.5 font-bold text-sm transition-all duration-200 data-[state=active]:bg-indigo-600 data-[state=active]:text-white dark:data-[state=active]:bg-indigo-600 dark:data-[state=active]:text-white w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.lecture_proficiency')}</span>
                        </TabsTrigger>
                    ) : null}

                    {textComprehensionQuestionsCount ? (
                        <TabsTrigger value="text_compreension" className="rounded-xl py-2.5 font-bold text-sm transition-all duration-200 data-[state=active]:bg-indigo-600 data-[state=active]:text-white dark:data-[state=active]:bg-indigo-600 dark:data-[state=active]:text-white w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.text_compreension')}</span>
                        </TabsTrigger>
                    ) : null}

                    {criticalThinkingQuestionsCount ? (
                        <TabsTrigger value="critical_thinking" className="rounded-xl py-2.5 font-bold text-sm transition-all duration-200 data-[state=active]:bg-indigo-600 data-[state=active]:text-white dark:data-[state=active]:bg-indigo-600 dark:data-[state=active]:text-white w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.critical_thinking')}</span>
                        </TabsTrigger>
                    ) : null}

                    {communicationAndProblemSolvingQuestionsCount ? (
                        <TabsTrigger value="communication_and_problem_solving" className="rounded-xl py-2.5 font-bold text-sm transition-all duration-200 data-[state=active]:bg-indigo-600 data-[state=active]:text-white dark:data-[state=active]:bg-indigo-600 dark:data-[state=active]:text-white w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.communication_and_problem_solving')}</span>
                        </TabsTrigger>
                    ) : null}

                    {industryAreaQuestionsCount ? (
                        <TabsTrigger value="specific_knowledge" className="rounded-xl py-2.5 font-bold text-sm transition-all duration-200 data-[state=active]:bg-indigo-600 data-[state=active]:text-white dark:data-[state=active]:bg-indigo-600 dark:data-[state=active]:text-white w-[20%] lg:w-auto">
                            <span className="truncate">{t('results.specific_knowledge')}</span>
                        </TabsTrigger>
                    ) : null}
                </TabsList>

                <TabsContent value="lecture_proficiency" className="w-full p-5 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100/50 dark:border-slate-900/30 rounded-3xl">
                    <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
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

                <TabsContent value="text_compreension" className="w-full p-5 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100/50 dark:border-slate-900/30 rounded-3xl">
                    <div className="mt-4 mb-8 max-w-md">
                        <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-1.5 tracking-wider">
                            <span>Classificação de Compreensão:</span>
                            <span className="text-indigo-600 font-extrabold">{textComprehensionQuestionsAccuracy.toFixed(0)}%</span>
                        </div>
                        <Scale 
                            selectedValue={checkResult(textComprehensionQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-500 sm:via-yellow-400 sm:to-emerald-500 sm:divide-x-2 sm:divide-white dark:sm:divide-slate-900"
                        />
                    </div>
                    
                    <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
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

                <TabsContent value="critical_thinking" className="w-full p-5 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100/50 dark:border-slate-900/30 rounded-3xl">
                    <div className="mt-4 mb-8 max-w-md">
                        <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-1.5 tracking-wider">
                            <span>Classificação de Pensamento Crítico:</span>
                            <span className="text-indigo-600 font-extrabold">{criticalThinkingQuestionsAccuracy.toFixed(0)}%</span>
                        </div>
                        <Scale 
                            selectedValue={checkResult(criticalThinkingQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-500 sm:via-yellow-400 sm:to-emerald-500 sm:divide-x-2 sm:divide-white dark:sm:divide-slate-900"
                        />
                    </div>
                    <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
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

                <TabsContent value="communication_and_problem_solving" className="w-full p-5 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100/50 dark:border-slate-900/30 rounded-3xl">
                    <div className="mt-4 mb-8 max-w-md">
                        <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-1.5 tracking-wider">
                            <span>Classificação de Resolução de Problemas:</span>
                            <span className="text-indigo-600 font-extrabold">{communicationAndProblemSolvingQuestionsAccuracy.toFixed(0)}%</span>
                        </div>
                        <Scale 
                            selectedValue={checkResult(communicationAndProblemSolvingQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-500 sm:via-yellow-400 sm:to-emerald-500 sm:divide-x-2 sm:divide-white dark:sm:divide-slate-900"
                        />
                    </div>
                    <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
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

                <TabsContent value="specific_knowledge" className="w-full p-5 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100/50 dark:border-slate-900/30 rounded-3xl">
                    <div className="mt-4 mb-8 max-w-md">
                        <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-1.5 tracking-wider">
                            <span>Classificação de Conhecimento Específico:</span>
                            <span className="text-indigo-600 font-extrabold">{industryAreaQuestionsAccuracy.toFixed(0)}%</span>
                        </div>
                        <Scale 
                            selectedValue={checkResult(industryAreaQuestionsAccuracy)} 
                            options={['low', 'medium', 'high']} 
                            classes="sm:bg-gradient-to-r sm:from-red-500 sm:via-yellow-400 sm:to-emerald-500 sm:divide-x-2 sm:divide-white dark:sm:divide-slate-900"
                        />
                    </div>
                    <div className="flex flex-col gap-5 md:grid md:grid-cols-2">
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

export default ExamResult;