import { useCallback, useEffect, useRef } from "react";
import { IExamsStore, IRecordStore } from "@/interfaces/store";
import { useExamsStore } from "@/store/exams";
import { toast } from 'react-toastify';
import { useParams, useRouter } from "next/navigation";
import { getProcessorSignedLink } from "@/services/processor";
import { useRecordStore } from "@/store/record";
import { uploadToGCS } from "@/services/gcs";
import { sendGCSUrl } from "@/services/exam";
import { BUTTON_NEXT, BUTTON_RECORD, BUTTON_STOP, MAX_RECORD_SECONDS, RECORD_STATE_INACTIVE, RECORD_STATE_RECORDING } from "@/constants/exams";
import { useAuth } from "@/context/auth";
import { STEP_EXAM_RECORD_BUTTON_NEXT, STEP_EXAM_RECORD_BUTTON_START, STEP_EXAM_RECORD_BUTTON_STOP } from "@/constants/tour";
import { useTranslations } from "next-intl";
import { Button } from "../ui/button";
import { cn } from "@/libs/shadcn/utils";
import { getMimeTypeFromBase64 } from "@/utils";
import { useLoading } from "@/context/loading";
import { isEmpty } from "lodash";
import { useQueryClient } from "@tanstack/react-query";
import { useRBAC } from "@/context/rbac";
import { SCOPE_USER, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { ChevronRightIcon, MicIcon, SquareIcon } from "lucide-react";

type TRecorderProps = {
    questions: any;
}

const Recorder : React.FC<TRecorderProps> = ({ questions }) => {    
    const MAX_RECORD_TIMEOUT = MAX_RECORD_SECONDS * 1000;
    
    // check browser mimetype 'audio/wav' or 'audio/x-wav'
    // const mime = ['audio/wav', 'audio/mpeg', 'audio/webm', 'audio/ogg', "avc1"].filter(MediaRecorder.isTypeSupported)[0];
    const mimeTypes = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/webm', 'audio/ogg', 'audio/mp4'];
    const supportedMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
    
    const mediabuttons : MediaRecorderOptions | any = { type: supportedMimeType };

    const queryClient = useQueryClient();
    const router = useRouter();    
    const { user } = useAuth();
    const params = useParams();
    const t = useTranslations();
    const { hasScopePermission } = useRBAC();
    const { setLoading } = useLoading();
    const { questionIndex, setExams } : IExamsStore = useExamsStore();
    const { audioChunks, audioURL, microphonePermission, stream, state, canStop, setRecord, setBlobData, getRecord } : IRecordStore = useRecordStore();
    
    const mediaRecorder = useRef<MediaRecorder | null>(null);
    const hasTimeout = useRef<any | null>(null);

    const isEducator = hasScopePermission([SCOPE_USER_IMPERSONATE]);
    const isStudent = hasScopePermission([SCOPE_USER]);

    const exam_id = params.id;
    const user_id = isEducator ? params.user_id : user?.user_id;

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

    const getMicrophonePermission = useCallback(async () => {
        if ("MediaRecorder" in window) {
            try {
                await navigator.mediaDevices.getUserMedia({
                    audio: true,
                    video: false,
                }).then(streamData => {
                    setRecord("microphonePermission", true);
                    setRecord("stream", streamData);
                });
            } catch (err) {
                console.error(err);
            }
        } else {
            console.error("The MediaRecorder API is not supported in your browser.");
        }
    }, [setRecord]);

    useEffect(() => {
        getMicrophonePermission();
    }, [getMicrophonePermission]);

    useEffect(() => {
        if (state === RECORD_STATE_RECORDING) {
            hasTimeout.current = setTimeout(() => {
                if (mediaRecorder && mediaRecorder.current) {
                    //stops the recording instance
                    mediaRecorder.current.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: supportedMimeType });
                        const audioUrl = URL.createObjectURL(audioBlob);

                        setRecord("audioURL", audioUrl);
                        setRecord('audioChunks', audioBlob);
                        setBlobData(audioBlob);
                        setRecord("state", RECORD_STATE_INACTIVE);
                        setExams("expanded", false);

                        clearTimeout(hasTimeout.current);
                    };
                    
                    mediaRecorder.current.stop();
                    toast.warn(t("toast.warnings.exam.record_exceeded_time"));
                }
                
            }, MAX_RECORD_TIMEOUT)
      
            return () => {
                clearTimeout(hasTimeout.current);
            }
        }
    }, [t, state, mediaRecorder, MAX_RECORD_TIMEOUT, audioChunks, audioURL, supportedMimeType, setBlobData, setRecord, setExams]);


    const record = () => {
        try {
            if (!microphonePermission) return getMicrophonePermission();

            const media = new MediaRecorder(stream as MediaStream, mediabuttons);
            
            mediaRecorder.current = media;
            mediaRecorder.current.start();

            setRecord("state", RECORD_STATE_RECORDING);
            setRecord("canStop", true);
            setRecord("seconds", MAX_RECORD_SECONDS - 1);
            setRecord("examID", exam_id); // store the examID to possible reset audio - only apply to student record flow (in case there are recorded backup data and the user change the exam)

            let localAudioChunks : Array<Blob> = [];
            mediaRecorder.current.ondataavailable = (event : BlobEvent) => {
                if (typeof event.data === "undefined") return;
                if (event.data.size === 0) return;
                localAudioChunks.push(event.data);
            };

            setRecord("audioChunks", localAudioChunks);
        } catch (error) {
            if (!microphonePermission) return toast.warn(t("toast.warnings.exam.warning_microphone_permission"));        
            toast.error(t("toast.errors.exam.error_record"));
            console.error(error)
        }
    };

    const stop = () => {
        try {
            if (!mediaRecorder || !mediaRecorder.current) throw new Error("no_media_recorder");
            
            clearTimeout(hasTimeout.current);
            
            mediaRecorder.current.stop();
            //stops the recording instance
            mediaRecorder.current.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: supportedMimeType });
                const audioUrl = URL.createObjectURL(audioBlob);

                setRecord("audioURL", audioUrl);
                setRecord('audioChunks', audioBlob);
                setBlobData(audioBlob);
                setRecord("state", RECORD_STATE_INACTIVE);
                setExams("expanded", false);

                clearTimeout(hasTimeout.current);
            };

            
            
        } catch (error) {
            toast.error(t("toast.errors.exam.error_stop_record"));  
            clear();
            console.error(error);
        }
    };

    const next = async () => {
        try {  
            if (!audioChunks || !mediaRecorder || !mediaRecorder.current) {
                try {
                    const base64Data: string | null = localStorage.getItem('audioData');
 
                    if (!base64Data) {
                        console.error("Error - could not recover audio");
                        toast.warning(t("toast.warnings.exam.warning_recovering_record"));   
                        return clear();
                    }
                    
                    try {
                        const data = base64Data.split(",");
                        const mimeType = getMimeTypeFromBase64(base64Data) as string;

                        const byteCharacters: string = atob(data[1]);
                        const byteArrays: Uint8Array[] = [];
                        
                        for (let i = 0; i < byteCharacters.length; i++) {
                            byteArrays.push(new Uint8Array([byteCharacters.charCodeAt(i)]));
                        }
                
                        const audioBlob: Blob = new Blob(byteArrays, { type: mimeType });
                        
                        setRecord("audioChunks", audioBlob);
                    } catch (error) {
                        // Handle decoding error
                        console.error('Error decoding base64 data:', error);
                        clear();
                    }
                    
                } catch (error) {
                    clear();
                    throw new Error("no_media_recorder");
                }
            }

            setLoading(true);

            if (questionIndex === undefined || !questions || isEmpty(questions) || !questions[questionIndex]) throw new Error("no_data");

            const hasNextQuestion = questionIndex < questions.length - 1;
            const question_id = questions[questionIndex].id;

            const processor = await getProcessorSignedLink(exam_id as string, user_id as string, question_id, supportedMimeType as string).catch(() => {
                toast.error(t("toast.errors.exam.error_sending_record"))
                setLoading(false)
            });
            if (!processor) return;
            
            const { signed_url } = processor;

            // asure to get localStorage blob if thats the case
            const audioToSend = getRecord().audioChunks;
            const upload = await uploadToGCS(signed_url, audioToSend, supportedMimeType as string).catch(() => {
                toast.error(t("toast.errors.exam.error_sending_record"))
                setLoading(false)
            });

            if (!upload) return;

            try {
                await sendGCSUrl(user_id as string, exam_id as string, question_id, signed_url)
                if (!hasNextQuestion) return endExam()

                setRecord("audioURL", "");
                setRecord("audioChunks", []);
                setRecord("canStop", false);
                setRecord("seconds", MAX_RECORD_SECONDS);

                setExams("questionIndex", questionIndex + 1)
                queryClient.invalidateQueries({ queryKey: ['questions'] });
                setLoading(false)
            } catch (error) {
                console.error(error)
                setLoading(false)
            }

            clearTimeout(hasTimeout.current);

            setLoading(false);
        } catch (error) {
            clearTimeout(hasTimeout.current);   
            console.error(error)
            toast.error(t("toast.errors.exam.error_sending_record"));    
            setLoading(false);
        }
    }

    const endExam = useCallback(() => {
        setLoading(true)
        setExams("questionIndex", 0);
        setExams("expanded", false);
        setRecord("audioURL", "");
        setRecord("audioChunks", []);
        setRecord("canStop", false);
        setRecord("seconds", MAX_RECORD_SECONDS);
        
        clearTimeout(hasTimeout.current);
        if (isStudent) {
            router.push(`/exams/${exam_id}/finish`);
            return; 
        }
        router.push(`/users/${user_id}/exams/${exam_id}/finish`);
    }, [setExams, setRecord, setLoading, isStudent, router, exam_id, user_id]);

    const isDisabled = useCallback((name : typeof BUTTON_STOP | typeof BUTTON_RECORD | typeof BUTTON_NEXT) => {
        switch (name) {
            case BUTTON_RECORD:
                if (state === RECORD_STATE_RECORDING) return true;
                if (audioURL) return true;
                return false;
            case BUTTON_STOP:
                if (!canStop) return true;
                if (state === RECORD_STATE_RECORDING) return false;
                return true;
            case BUTTON_NEXT:
                if (state === RECORD_STATE_RECORDING) return true;
                if (audioURL) return false;
                return true;
            default:
                return true;
        }
    }, [state, audioURL, canStop]);

    const getMessage = (name: typeof BUTTON_STOP | typeof BUTTON_RECORD | typeof BUTTON_NEXT ) => {
        if (!mediaRecorder || !mediaRecorder.current) return name;

        switch (name) {
            case BUTTON_RECORD:
                if (mediaRecorder.current.state === RECORD_STATE_RECORDING) return "recording_state";
            case BUTTON_STOP:
                if (mediaRecorder.current.state === RECORD_STATE_RECORDING) return "stop_recording_state";
            // case 'next':
            //     if (mediaRecorder.current.state === "recording") return "";
            default:
                return name;
        }
    }

    return (
        <>
            <div className="w-full flex justify-center gap-10 md:gap-20 lg:gap-20 items-center h-fit">
                <div className="flex flex-col gap-2 justify-center items-center">
                    <Button 
                        data-step={STEP_EXAM_RECORD_BUTTON_STOP}
                        className={cn(
                            'rounded-full dark:bg-darkPrimary bg-primary text-white',
                            'w-14 h-14 sm:w-[80px] sm:h-[80px]',
                            isDisabled(BUTTON_STOP) && 'cursor-not-allowed',
                        )}
                        disabled={isDisabled(BUTTON_STOP)}
                        onClick={stop}
                    >
                        <SquareIcon fill="#fff" color="white" size={28}/>
                    </Button>
                    <span className="hidden sm:block text-sm">
                        {t(`exam.buttons.${getMessage(BUTTON_STOP)}`)}
                    </span>
                </div>

                <div className="flex flex-col gap-2 justify-center items-center">
                    <Button 
                        data-step={STEP_EXAM_RECORD_BUTTON_START}
                        className={cn(
                            'relative rounded-full dark:bg-darkPrimary bg-primary text-white',
                            'w-20 h-20 sm:w-[140px] sm:h-[140px]',
                            state === RECORD_STATE_RECORDING ? 'animate-pulse ' : '',
                            isDisabled(BUTTON_RECORD) && 'cursor-not-allowed',
                        )}
                        disabled={isDisabled(BUTTON_RECORD)}
                        onClick={record}
                    >
                        <MicIcon color="white" size={48} />
                        {state === "recording" && !audioURL ? 
                            <div className="absolute right-0 top-1/4">
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-destructive"></span>
                                </span>
                            </div>
                            : 
                            null
                        }
                    </Button>
                    <span className="hidden sm:block text-sm">
                        {t(`exam.buttons.${getMessage(BUTTON_RECORD)}`)}
                    </span>
                </div>

                <div className="flex flex-col gap-2 justify-center items-center">
                    <Button 
                        data-step={STEP_EXAM_RECORD_BUTTON_NEXT}
                        className={cn(
                            'rounded-full dark:bg-darkPrimary bg-primary text-white',
                            'w-14 h-14 sm:w-[80px] sm:h-[80px]',
                            isDisabled(BUTTON_NEXT) && 'cursor-not-allowed',
                        )}
                        disabled={isDisabled(BUTTON_NEXT)}
                        onClick={next}
                    >
                        <ChevronRightIcon size={36} color="white" />
                    </Button>
                    <span className="hidden sm:block text-sm">
                        {t(`exam.buttons.${getMessage(BUTTON_NEXT)}`)}
                    </span>
                </div>
            </div>
        </>
    )
}

export default Recorder;