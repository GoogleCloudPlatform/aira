import { Button } from "@/components/ui/button";
import { TFormDeleteProps } from "@/interfaces/component";
import { useQueryClient } from "@tanstack/react-query";
import { MODE_DELETE } from "@/constants";
import { useTranslations } from "next-intl";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface CustomFormDeleteProps extends TFormDeleteProps {
    t_prefix: string;
}

const FormDelete : React.FC<CustomFormDeleteProps> = ({ mode, title, formData, setOpen, t_prefix }) => {

    const t = useTranslations(t_prefix as any);
    const queryClient = useQueryClient();
    
    const handleConfirmDeletion = async () => {
        await formData.confirm();
        setOpen(false)
        queryClient.invalidateQueries({ queryKey: [formData.category] });
    }

    return (
        <>
            <Dialog open={mode === MODE_DELETE} onOpenChange={setOpen}>
                <DialogContent className="max-w-[300px] sm:max-w-[525px] dark:text-white">
                    <DialogHeader>
                        <DialogTitle>{t('title')}</DialogTitle>
                    </DialogHeader>
                    <section className="dark:text-white">
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

export default FormDelete;
