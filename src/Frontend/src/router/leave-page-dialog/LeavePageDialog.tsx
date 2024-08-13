import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { RBACWrapper } from "@/context/rbac";
import { useTranslations } from "next-intl";
import { Dispatch, SetStateAction } from "react";

type TProps = {
    open: boolean;
    onOpenChange: Dispatch<SetStateAction<boolean>>,
    onConfirmation: () => void;
}

const LeavePageDialog : React.FC<TProps> = ({ open, onOpenChange, onConfirmation }) => {
    const t = useTranslations("dialog");

    return (
        <>
            <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                <Dialog 
                    open={open}
                    onOpenChange={onOpenChange}
                >
                    <DialogContent className="sm:max-w-[525px] dark:text-white">
                        <DialogHeader>
                            <DialogTitle>{t("warning")}</DialogTitle>
                        </DialogHeader>
                        
                        <section>
                            <div className="space-y-2 dark:text-white">
                                <p>{t("leave_page_message_1")}</p>
                                <p>{t("leave_page_message_2")}</p>
                                <br />
                                <p><b>{t("leave_page_message_3")}</b></p>
                            </div>
                        </section>

                        <DialogFooter className="flex flex-col gap-2 md:flex-row">
                            <Button type="button" onClick={() => onOpenChange(false)}>
                                {t("buttons.close")}
                            </Button>
                            <Button type="button" onClick={() => onConfirmation()}>
                                {t("buttons.confirm")}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </RBACWrapper>
        </>
    )
}

export default LeavePageDialog;