import { ICON_ARROW_PATH, ICON_ARROW_RIGHT } from "@/constants/icons";
import { SCOPE_ADMIN, SCOPE_LEARNER } from "@/constants/rbac";
import { RBACWrapper } from "@/context/rbac";
import useIcon from "@/hooks/useIcon/useIcon";
import { IUser } from "@/interfaces/user";
import { useExamsStore } from "@/store/exams";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

const FinishExam : React.FC = () => {
    const router = useRouter();
    
    const { t } = useTranslation();
    const { finished, setExams } = useExamsStore();   
    const { getIcon } = useIcon();

    const handleClick = () => {
        setExams("finished", false);
        router.push("/home");
    }

    if (!finished) return <div className="w-full h-full flex items-center justify-center">{t("redirecting", { ns: "exam" })}...</div>;

    const getText = () => {
        const user : string | null = localStorage.getItem("user");
        if (!user) return "";
        
        const { email, user_name } = JSON.parse(user);
        
        const text = user_name ? user_name : email;

        return text + ", ";
    }

    return (
        <>
            <div className="flex items-center justify-center h-full w-full">
                <div className="flex flex-col justify-around p-5 h-full w-full">
                    <div className="flex flex-col gap-5">
                        <div className="flex justify-center items-center">
                            <span className="text-4xl">{t("success_message", { ns: "exam" })}!</span>
                        </div>
                        <div className="flex flex-col items-center justify-center text-center gap-5">
                            <p>{getText()} {t("audio_success_record", { ns: "exam" })}.</p>
                            <p>{t("analisys_message", { ns: "exam" })}.</p>
                        </div>
                    </div>
                    <div className="flex flex-col gap-5 items-center justify-center">
                        
                        <div 
                            onClick={() => router.push("/exams")}
                            className="w-24 h-24 bg-green-200 hover:bg-green-100 rounded-full flex items-center justify-center border border-gray-300 cursor-pointer"
                        >
                            <div className="w-14 h-14">
                                {getIcon({ icon: ICON_ARROW_PATH, classes: "text-green-500" })}
                            </div>
                        </div>
                    
                        <div>
                            {t("start_again", { ns: "exam" })}
                        </div>

                        {/* <RBACWrapper requiredScopes={[SCOPE_LEARNER]}>
                            <div onClick={handleClick} className="cursor-pointer text-blue-500">
                                {t("show_results", { ns: "exam" })}
                            </div>
                        </RBACWrapper> */}

                    </div>
                </div>
            </div>
        </>
    )
}

export default FinishExam;