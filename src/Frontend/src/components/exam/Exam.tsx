import Recorder from "../recorder/Recorder";
import { IExamResponse } from "@/interfaces/exams";
import useTyping from "@/hooks/useTyping/useTyping";
import { useExamsStore } from "@/store/exams";
import { useRecordStore } from "@/store/record";
import { IExamsStore, IRecordStore } from "@/interfaces/store";
import { RBACWrapper } from "@/context/rbac";
import { SCOPE_ADMIN, SCOPE_LEARNER, SCOPE_USER } from "@/constants/rbac";
import { useTranslation } from "react-i18next";
import { useEffect, useRef } from "react";
import NoData from "../no-data/NoData";
import useIcon from "@/hooks/useIcon/useIcon";
import { MAX_RECORD_SECONDS, QUESTION_STATUS_NOT_STARTED, QUESTION_TYPE_PHRASES } from "@/constants/exam";
import { ICON_ARROWS_POINTING_IN, ICON_ARROWS_POINTING_OUT } from "@/constants/icons";

const Exam : React.FC<IExamResponse | any> = ({ exam }) => {
    const containerRef = useRef(null);
    const { t } = useTranslation();
    const { Visor, GridVisor } = useTyping();
    const { getIcon } = useIcon();
    const { expanded, questionIndex, setExams } : IExamsStore = useExamsStore();
    const { state, seconds, setRecord } : IRecordStore = useRecordStore();
    const hasTimeout = useRef<any | null>(null);

    // jump to next question if current question is different from not_started
    useEffect(() => {
        if (exam && exam[questionIndex]) {
            if (exam[questionIndex].status !== QUESTION_STATUS_NOT_STARTED) {
                setExams("questionIndex", questionIndex + 1);
            }
        }
    }, [exam, questionIndex, setExams]);

    useEffect(() => {
        
        const countdown = () => {
            if (seconds > 0 && seconds < MAX_RECORD_SECONDS && state === "recording") {
                hasTimeout.current = setTimeout(() => {
                    setRecord("seconds", seconds - 1)
                }, 1000);
            }
        }

        countdown();
        
        return () => {
            clearTimeout(hasTimeout.current);
        }
    }, [state, seconds, setRecord, setExams]);

    if (!exam) return <NoData />;
    if (!exam.length) return <NoData message="warning_no_questions" />;
    if (!exam[questionIndex]) return <NoData />;
    
    const { id, data, name, type } = exam[questionIndex];

    return (
        <>
            <RBACWrapper requiredScopes={[SCOPE_LEARNER, SCOPE_ADMIN, SCOPE_USER]}>
                <div className='flex flex-col items-center h-full sm:gap-5 gap-1'>
                    <div className='text-2xl sm:mt-10 mt-3 flex-shrink w-full items-center justify-center flex'>
                        <span>{t("question", { ns: "exam" })} {questionIndex + 1} {t("of", { ns: "exam" })} {exam.length}</span>
                    </div>
                    <div className='w-full py-2 px-2 sm:w-4/5 sm:h-2/6 h-4/6 flex flex-col flex-grow sm:gap-5 gap-2 text-center'>
                        <span className="text-xs sm:text-sm">{t("top_message", { ns: "exam" })}</span>
                        
                        
                        <div className="sm:h-2/6 h-5/6 flex flex-col flex-grow">
                            <div className="w-full p-1 flex justify-end">
                                <div className="w-5 h-5 cursor-pointer" onClick={() => setExams("expanded", true)}>
                                    {getIcon({ icon: expanded ? ICON_ARROWS_POINTING_IN : ICON_ARROWS_POINTING_OUT, classes: "" })}
                                </div>
                            </div>
                            
                            <div ref={containerRef} className={`w-full h-full overflow-hidden z-10 
                                ${expanded ? "z-10 absolute left-0 pb-10 px-5 sm:p-20 top-0 backdrop-blur-lg" : ""}`
                            }>
                                {expanded ? 
                                    <div className="flex w-full p-1 justify-end">
                                        <div className="w-5 h-5 cursor-pointer" onClick={() => setExams("expanded", false)}>
                                            {getIcon({ icon: expanded ? ICON_ARROWS_POINTING_IN : ICON_ARROWS_POINTING_OUT, classes: "" })}
                                        </div>
                                    </div> 
                                    : 
                                    null
                                }
                                {type === QUESTION_TYPE_PHRASES ? <Visor>{data}</Visor> : <GridVisor words={data} />}
                            </div>

                            <span className="flex-shrink justify-end text-gray-400 flex text-sm sm:text-base">{seconds} {t("seconds", { ns: "exam" })}</span>

                            <span className="flex-shrink text-xs sm:text-sm hidden sm:flex justify-center">{t("bottom_message", { ns: "exam" })}</span>
                        </div>
                    
                        
                    </div>
                    
                    <div className='w-full flex items-center justify-center h-auto flex-shrink sm:p-10'>
                        <Recorder />
                    </div>
                </div>
            </RBACWrapper>
        </>
    )
}

export default Exam;