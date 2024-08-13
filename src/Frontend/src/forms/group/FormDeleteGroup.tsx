import { Button } from "@/components/ui/button";
import { TFormDeleteProps } from "@/interfaces/component";
import { useQueryClient } from "@tanstack/react-query";
import { CATEGORY_GROUPS, MODE_DELETE } from "@/constants";
import { useTranslations } from "next-intl";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const FormDeleteGroup : React.FC<TFormDeleteProps> = ({ mode, title, formData, setOpen }) => {

    const t = useTranslations("form.group.delete");
    const queryClient = useQueryClient();
    const handleConfirmDeletion = async () => {
        await formData.confirm();
        setOpen(false)
        queryClient.invalidateQueries({ queryKey: [CATEGORY_GROUPS] });
    }

    return (
        <>
            <Dialog open={mode === MODE_DELETE} onOpenChange={setOpen}>
                <DialogContent className="max-w-[300px] sm:max-w-[525px] dark:text-white">
                    <DialogHeader>
                        <DialogTitle>{t(title)}</DialogTitle>
                    </DialogHeader>
                    <section> 
                        {t('message')}
                    </section>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button type="button" onClick={() => setOpen(false)}>
                            {t('close')}
                        </Button>
                        <Button type="button" onClick={handleConfirmDeletion}>
                            {t('confirm')}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    )
}

export default FormDeleteGroup;