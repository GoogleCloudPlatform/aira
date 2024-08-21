'use client'

import { SCOPE_USER, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { RBACWrapper, useRBAC } from "@/context/rbac";
import { Suspense, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import UsersCarousel from "../users-carousel/UsersCarousel";
import { ChevronRight, Undo2Icon } from "lucide-react";
import Loading from "../loading/Loading";

const ExamFinish : React.FC = () => {
    const [open, setOpen] = useState<boolean>(false);

    const router = useRouter();
    const t = useTranslations('exam');
    const { hasScopePermission } = useRBAC();

    const handleClick = () => {
        if (hasScopePermission([SCOPE_USER])) router.push("/exams");
        if (hasScopePermission([SCOPE_USER_IMPERSONATE])) router.push("/users/exams");
    }

    const getText = () => {
        const user : string | null = localStorage.getItem("user");
        if (!user) return "";
        
        const { email, user_name } = JSON.parse(user);
        
        const text = user_name ? user_name : email;
        
        let message = `${text}, ${t("messages.audio_success_record")}.`;
        if (hasScopePermission([SCOPE_USER_IMPERSONATE])) message += ` (${t("messages.recorded_as_impersonate")})`;

        return message;
    }

    return (
        <>
            <section className="flex flex-col items-center h-full w-full gap-10">
                <div className="flex flex-col p-5 justify-around w-full">
                    <div className="flex flex-col gap-5">
                        <div className="flex justify-center items-center">
                            <span className="text-4xl text-primary dark:text-white">{t("messages.success_message")}!</span>
                        </div>
                        <div className="flex flex-col items-center justify-center text-center gap-5">
                            <p>{getText()}</p>
                            <p>{t("messages.analisys_message")}.</p>
                        </div>
                    </div>
                    <div className="grid grid-flow-col gap-10 items-center justify-center mt-20">
                        <div className="flex flex-col gap-3 items-center justify-center">
                            <button onClick={handleClick} className="text-white w-12 h-12 bg-primary dark:bg-darkPrimary flex items-center justify-center rounded-full">
                                <Undo2Icon />
                            </button>
                            <div className="">
                                {t("buttons.start_again")}
                            </div>
                        </div>

                        <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                            <div className="flex flex-col gap-3 items-center justify-center">
                                <button onClick={()=> setOpen(true)} className="text-white w-12 h-12 bg-primary dark:bg-darkPrimary flex items-center justify-center rounded-full">
                                    <ChevronRight size={24} strokeWidth={3} />
                                </button>
                                <div>
                                    {t("buttons.next_student")}
                                </div>
                            </div>
                        </RBACWrapper>
                    </div>                  
                </div>
                
                <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                    <Suspense fallback={<Loading style="vertical" text={true}/>}>
                        {open ? <UsersCarousel open={open} setOpen={setOpen} />  : null}      
                    </Suspense>
                </RBACWrapper>
                
            </section>
        </>
    )
}

export default ExamFinish;