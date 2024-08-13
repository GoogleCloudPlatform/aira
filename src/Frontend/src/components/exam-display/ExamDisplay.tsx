'use client'

import { ENUM_QUESTION_STATUS_NOT_STARTED } from "@/constants/enums";
import { MAX_RECORD_SECONDS, QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_PHRASES, RECORD_STATE_INACTIVE } from "@/constants/exams";
import { ICON_ARROWS_POINTING_IN, ICON_ARROWS_POINTING_OUT } from "@/constants/icons";
import { SCOPE_USER, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { STEP_EXAM_QUESTION_INFO, STEP_EXAM_TIMER, STEP_EXAM_VISOR, STEP_EXAM_VISOR_EXPAND } from "@/constants/tour";
import { RBACWrapper, useRBAC } from "@/context/rbac";
import useIcon from "@/hooks/useIcon";
import { IExamsStore, IRecordStore } from "@/interfaces/store";
import { cn } from "@/libs/shadcn/utils";
import { getExamQuestionsByUser} from "@/services/exam";
import { useExamsStore } from "@/store/exams";
import { useQuery } from "@tanstack/react-query";
import { isEmpty } from "lodash";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRecordStore } from "@/store/record";
import Recorder from "../recorder/Recorder";
import { useLoading } from "@/context/loading";
import SkeletonExam from "../skeletons/SkeletonExam";
import { useRouter } from "next/navigation";
import TextVisor from "../text-visor/TextVisor";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { MicrophoneTesterWrapper } from "../microphone-tester/MicrophoneTester";
import { Button } from "../ui/button";
import Tour from "../tour/Tour";
import { STEPS_EXAM } from "@/libs/tour/react-tour";
import { useBackButtonNavigation } from "@/router/navigation-block/NavigationBlock";
import { ENDPOINT_EXAMS, ENDPOINT_USERS } from "@/constants/endpoints";
import { toast } from "react-toastify";
import LeavePageDialog from "@/router/leave-page-dialog/LeavePageDialog";
import QuestionsVisor from "../visors/QuestionsVisor";
import AnswersForm from "../../forms/multiple-choice/FormMultipleChoice";

type TExamDisplayProps = {
    user_id: string;
    exam_id: string;
}

const ExamDisplay : React.FC<TExamDisplayProps> = ({ user_id, exam_id }) => {
    const [microphoneTester, setMicrophoneTester] = useState<boolean>(true);
    const [showLeaveDialog, setShowLeaveDialog] = useState<boolean>(false);

    const t = useTranslations();
    const router = useRouter();
    const { loading, setLoading } = useLoading();
    const { getIcon } = useIcon();
    const { expanded, questionIndex, setExams } : IExamsStore = useExamsStore();
    const { state, seconds, setRecord, getRecord } : IRecordStore = useRecordStore();
    const { hasScopePermission } = useRBAC();
    const hasTimeout = useRef<any | null>(null);

    const isEducator = hasScopePermission([SCOPE_USER_IMPERSONATE]);
    const isStudent = hasScopePermission([SCOPE_USER]);

    useBackButtonNavigation((ev: Event) => {
        ev.preventDefault();
        setShowLeaveDialog(true);
    });

    const confirmLeavePage = () => {
        if (!isEducator) return null;
        router.push('/users/exams');
    }

    // resets question index
    useEffect(() => {
        return () => {
            setExams("questionIndex", 0)
            setLoading(false)
        };
    }, [setExams, setLoading]);

    const clear = useCallback(() => {
        localStorage.setItem("audioData", ""); // clear backup audio on storage to avoid unwanted behavior/saving on api post
        setRecord("examID", "");
        setExams("expanded", false);
        setRecord("audioURL", "");
        setRecord("audioChunks", []);
        setRecord("canStop", false);
        setRecord("state", RECORD_STATE_INACTIVE);
        setRecord("seconds", MAX_RECORD_SECONDS);
        setLoading(false);
    }, [setExams, setRecord, setLoading]);

    // clear record on unmount
    useEffect(() => {
        return () => {
            if (isEducator) {
                clear();
            } else { // student
                const hasRecord = localStorage.getItem("audioData");
                if (hasRecord) {
                    const currentExamId = exam_id;
                    const recordExamID = getRecord().examID;
                    if (currentExamId !== recordExamID) {
                        clear();
                    }
                }
            }
        }
    }, [isEducator, clear, getRecord, exam_id]);

    const { data: questions, isLoading, isError } = useQuery({ 
        queryKey: ['questions', exam_id],
        queryFn: () => getExamQuestionsByUser({ user_id, exam_id })
    });

    // controls questions
    useEffect(() => {
        if (questions) {
            const notStarted = questions?.find((question: { status: string }) => question.status === ENUM_QUESTION_STATUS_NOT_STARTED)

            if (notStarted) return setExams('questionIndex', notStarted.order -1)
            
            if (!notStarted) {
                if (isStudent) {
                    router.push(`/${ENDPOINT_EXAMS}/${exam_id}/finish`);
                    return;
                }

                router.push(`/${ENDPOINT_USERS}/${user_id}/${ENDPOINT_EXAMS}/${exam_id}/finish`);
            }
        }        
    }, [questions, user_id, exam_id, router, setExams, isStudent]);

    // control timer
    useEffect(() => {
        const countdown = () => {
            if (
                seconds > 0 &&
                seconds < MAX_RECORD_SECONDS &&
                state === 'recording'
            ) {
                hasTimeout.current = setTimeout(() => {
                    setRecord('seconds', seconds - 1);
                }, 1000);
            }
        };

        countdown();

        return () => {
            clearTimeout(hasTimeout.current);
        };
    }, [state, seconds, setRecord]);

    const checkMicrophonePermissions = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            return stream;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            return null;
        }
    };

    const close = useCallback(async () => {
        const microphoneStream = await checkMicrophonePermissions();

        if (!microphoneStream) return toast.warn(t('toast.warnings.exam.warning_microphone_permission'));

        setMicrophoneTester(false);
    }, [t]);

    if (!questions || isEmpty(questions)) return <SkeletonExam />;
    if (isLoading || loading) return <SkeletonExam />;
    if (!questions[questionIndex]) return <>No Question</>;
    if (isError) return <>could not load data</>

    const { formatted_data, type } = questions[questionIndex];

    return (
        <>
            <RBACWrapper requiredScopes={[SCOPE_USER, SCOPE_USER_IMPERSONATE]}>
                <LeavePageDialog 
                    open={showLeaveDialog}
                    onOpenChange={setShowLeaveDialog}
                    onConfirmation={confirmLeavePage}
                />

                {type !== QUESTION_TYPE_MULTIPLE_CHOICE && (
                    <>
                        <Tour steps={STEPS_EXAM} />
                        <Dialog open={microphoneTester} onOpenChange={close}>
                            <DialogContent className="sm:max-w-[525px] dark:bg-darkBackground border-border dark:border-darkBorder">
                                <DialogHeader> 
                                    <DialogTitle className="text-primary dark:text-white">{t("exam.titles.exam_instructions")}</DialogTitle>
                                </DialogHeader>
                                
                                <MicrophoneTesterWrapper />

                                <DialogFooter>
                                    <Button type="button" className="text-white bg-primary dark:bg-darkPrimary" onClick={close}>{t("exam.buttons.close")}</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </>
                )}

                <article className="h-full flex overflow-y-auto [&::-webkit-scrollbar]:hidden flex-col dark:text-white text-black">
                    <section className='text-2xl w-full items-center justify-center flex flex-col gap-2' data-step={STEP_EXAM_QUESTION_INFO}>
                        <span>{t("exam.titles.question")} {questionIndex + 1} {t("exam.titles.of")} {questions.length}</span>
                        {type === QUESTION_TYPE_MULTIPLE_CHOICE ? (
                            <span className="text-xs sm:text-sm text-center">{t("exam.messages.top_message_multiple_choice")}</span>
                        ) : (
                            <span className="text-xs sm:text-sm text-center">{t("exam.messages.top_message")}</span>
                        ) }
                    </section>

                    <section className={`flex flex-col container gap-2 ${type === QUESTION_TYPE_MULTIPLE_CHOICE ? 'min-h-[300px] max-h-[300px]' : 'flex-grow'}`}>                                           
                        <div className="w-full flex justify-end">
                            <div className="w-5 h-5 cursor-pointer" onClick={() => setExams("expanded", !expanded)} data-step={STEP_EXAM_VISOR_EXPAND}>
                                {getIcon({ icon: expanded ? ICON_ARROWS_POINTING_IN : ICON_ARROWS_POINTING_OUT })}
                            </div>
                        </div>

                        <div 
                            data-step={STEP_EXAM_VISOR}
                            className={cn(
                                'w-full flex h-full overflow-y-hidden',
                                expanded && 'w-full z-50 absolute left-0 pb-10 px-5 sm:p-10 top-0 backdrop-blur-lg',
                                type === QUESTION_TYPE_PHRASES ? 'sm:flex sm:justify-center' : 'w-full'
                            )}
                        >
                            <div className="w-full h-full">
                                {expanded ? 
                                    <div className="flex w-full p-1 justify-end">
                                        <div className="w-5 h-5 cursor-pointer" onClick={() => setExams("expanded", false)}>
                                            {getIcon({ icon: expanded ? ICON_ARROWS_POINTING_IN : ICON_ARROWS_POINTING_OUT, classes: "" })}
                                        </div>
                                    </div> 
                                    : 
                                    null
                                }

                                <section className={cn(
                                    'p-4 w-full h-full rounded-lg border border-border dark:border-darkBorder overflow-y-auto',
                                    expanded ? 'max-h-[85vh] bg-background dark:bg-darkBackground' : type !== QUESTION_TYPE_MULTIPLE_CHOICE ? 'max-h-[calc(100vh-370px)] sm:max-h-[calc(100vh-420px)]' : 'max-h-[300px]',
                                )}>
                                    {type === QUESTION_TYPE_PHRASES ? 
                                        <TextVisor data={formatted_data} /> :
                                        <QuestionsVisor question={questions[questionIndex]} />
                                    }
                                </section>

                                {type !== QUESTION_TYPE_MULTIPLE_CHOICE && (
                                    <div className="w-full flex justify-end text-sm my-2">
                                        <span data-step={STEP_EXAM_TIMER}>{seconds} {t("exam.messages.seconds")}</span>
                                    </div>

                                )}
                            </div>
                        </div>
                    </section>
                    
                    {type === QUESTION_TYPE_MULTIPLE_CHOICE ? (
                        <div className="flex-1 p-8 max-w-[1400px] mx-auto w-full">
                            <AnswersForm question={questions[questionIndex]} total_questions={questions.length} />
                        </div>
                    ) : (
                        <div className="mt-2">
                            <span className="mb-4 sm:mb-6 text-xs sm:text-sm w-full flex justify-center text-center">{t("exam.messages.bottom_message")}</span>
                            <Recorder questions={questions} />
                        </div>
                    )}
                </article>
            </RBACWrapper>
        </>
    )
}

export default ExamDisplay;