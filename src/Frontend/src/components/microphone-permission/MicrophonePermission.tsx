'use client'

import { useTranslations } from "next-intl";
import { useCallback, useEffect } from "react";
import { toast } from "react-toastify";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Button } from "../ui/button";
import { useRecordStore } from "@/store/record";
import { MicrophoneTester, MicrophoneTesterWrapper } from "../microphone-tester/MicrophoneTester";
import { LucideInfo } from "lucide-react";
import { MICROPHONE_DIALOG_TIPS } from "@/constants/exams";

const MicrophonePermission : React.FC = () => {
    const t = useTranslations();
    const { microphonePermission, setRecord } = useRecordStore();

    const checkMicrophonePermissions = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            return stream;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            return null;
        }
    };

    useEffect(() => {
        const getMicrophonePermission = async () => {
            const hasPermission = await checkMicrophonePermissions();
            if (!hasPermission) {
                setRecord("microphonePermission", false);
            }
        }

        getMicrophonePermission();
    }, [setRecord]);

    const close = useCallback(async () => {
        const microphoneStream = await checkMicrophonePermissions();

        if (!microphoneStream) {
            return toast.warn(t('toast.warnings.exam.warning_microphone_permission'));
        }

        setRecord("microphonePermission", true);
    }, [t, setRecord]);

    if (microphonePermission) return null;

    return (
        <>
            <Dialog open={!microphonePermission} onOpenChange={close}>
                <DialogContent className="sm:max-w-[525px]">
                    <DialogHeader>
                        <DialogTitle>Exams Instructions</DialogTitle>
                        here?
                    </DialogHeader>
                    
                    <MicrophoneTesterWrapper />

                    <DialogFooter>
                        <Button type="button" className="text-white" onClick={close}>close</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    )
}

export default MicrophonePermission;