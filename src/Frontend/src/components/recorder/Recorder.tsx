// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { useCallback, useEffect, useRef } from "react";
import Button from "../button/Button";
import { IButton } from "@/interfaces/button";
import { IExamsStore, IRecordStore } from "@/interfaces/store";
import { useExamsStore } from "@/store/exams";
import { toast } from 'react-toastify';
import { i18n, useTranslation } from 'next-i18next';
import { useRouter } from "next/router";
import { ICON_ARROW_RIGHT, ICON_MICROPHONE, ICON_STOP } from "@/constants/icons";
import { getProcessorSignedLink } from "@/services/processor";
import { useRecordStore } from "@/store/record";
import { uploadToGCS } from "@/services/gcs";
import { sendGCSUrl } from "@/services/exams";
import { mutate } from "swr";
import { ENDPOINT_EXAMS } from "@/constants/endpoint";
import { useSettingsStore } from "@/store/settings";
import { IQuestion } from "@/interfaces/question";
import { ParsedUrlQuery } from "querystring";
import { MAX_RECORD_SECONDS } from "@/constants/exam";
import { getMimeTypeFromBase64 } from "@/utils";

const Recorder : React.FC = () => {
    const MAX_RECORD_TIMEOUT = MAX_RECORD_SECONDS * 1000;
    
    // check browser mimetype 'audio/wav' or 'audio/x-wav'
    const mime = ['audio/wav', 'audio/mpeg', 'audio/webm', 'audio/ogg'].filter(MediaRecorder.isTypeSupported)[0];
    
    const mediabuttons : MediaRecorderOptions | any = { type: mime };
    const buttons : Array<IButton> = [
        { name: "stop", action: () => stop(), size: 100, icon: ICON_STOP, classes: "row-start-2 col-start-1 col-end-2 sm:row-start-1 sm:col-start-1 sm:col-end-1" },
        { name: "record", action: () => record(), size: 150, icon: ICON_MICROPHONE, classes: "row-start-1 col-start-2 col-end-3 sm:row-start-1 sm:col-start-2 sm:col-end-2" },
        { name: "next", action: () => next(), size: 100, icon: ICON_ARROW_RIGHT, classes: "row-start-2 col-start-3 col-end-3 sm:row-start-1 sm:col-start-3 sm:col-start-3" },
    ];

    const router = useRouter();
    const { id } : ParsedUrlQuery = router.query;

    const { t } = useTranslation();
    const { setSettings } = useSettingsStore();
    const { exam, questionIndex, setExams } : IExamsStore = useExamsStore();
    const { audioChunks, audioURL, microphonePermission, stream, state, canStop, setRecord, setBlobData, getRecord } : IRecordStore = useRecordStore();
    
    const mediaRecorder = useRef<MediaRecorder | null>(null);
    const hasTimeout = useRef<any | null>(null);

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
    }, [getMicrophonePermission, setRecord]);

    useEffect(() => {
        if (state === "recording") {
            hasTimeout.current = setTimeout(() => {
                if (mediaRecorder && mediaRecorder.current) {
                    //stops the recording instance
                    mediaRecorder.current.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: mime });
                        const audioUrl = URL.createObjectURL(audioBlob);

                        setRecord("audioURL", audioUrl);
                        setRecord('audioChunks', audioBlob);
                        setBlobData(audioBlob);
                        setRecord("state", "inactive");
                        setExams("expanded", false);

                        clearTimeout(hasTimeout.current);
                    };
                    
                    mediaRecorder.current.stop();
                    toast.warn(i18n?.t('record_exceeded_time', { ns: "toast" }));
                }
                
            }, MAX_RECORD_TIMEOUT)
      
            return () => {
                clearTimeout(hasTimeout.current);
            }
        }
    }, [state, mediaRecorder, MAX_RECORD_TIMEOUT, audioChunks, audioURL, mime, setBlobData, setRecord, setExams]);


    const record = () => {
        try {
            if (!microphonePermission) return getMicrophonePermission();

            const media = new MediaRecorder(stream as MediaStream, mediabuttons);
            
            mediaRecorder.current = media;
            mediaRecorder.current.start();

            setRecord("state", "recording");
            setRecord("canStop", true);
            setRecord("seconds", MAX_RECORD_SECONDS - 1);

            let localAudioChunks : Array<Blob> = [];
            mediaRecorder.current.ondataavailable = (event : BlobEvent) => {
                if (typeof event.data === "undefined") return;
                if (event.data.size === 0) return;
                localAudioChunks.push(event.data);
            };

            setRecord("audioChunks", localAudioChunks);

            // //stop audio after max record time
            // hasTimeout.current = setTimeout(() => {
            //     toast.warn(i18n?.t('record_exceeded_time', { ns: "toast" }))
            //     stop();
            // }, MAX_RECORD_TIMEOUT);

        } catch (error) {
            if (!microphonePermission) return toast.warn(i18n?.t('warning_microphone_permission'));        
            toast.error(i18n?.t('error_record'));
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
                const audioBlob = new Blob(audioChunks, { type: mime });
                const audioUrl = URL.createObjectURL(audioBlob);

                setRecord("audioURL", audioUrl);
                setRecord('audioChunks', audioBlob);
                setBlobData(audioBlob);
                setRecord("state", "inactive");
                setExams("expanded", false);

                clearTimeout(hasTimeout.current);
            };

            
            
        } catch (error) {
            toast.error(i18n?.t('error_stop_record'));  
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
                        toast.warning(i18n?.t('warning_recovering_record', { ns: "toast" }));   
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
                    throw new Error("no_media_recorder");
                }
            }

            setSettings("loading", true);

            if (questionIndex === undefined || !exam || !(exam as Array<IQuestion>).length || !(exam as Array<IQuestion>)[questionIndex]) throw new Error("no_data");

            const hasNextQuestion = questionIndex! < (exam as Array<IQuestion>).length! - 1;
            const question_id = (exam as Array<IQuestion>)[questionIndex].id;

            const processor = await getProcessorSignedLink(id as string, question_id, mime).catch(() => {
                toast.error(t("error_sending_record", { ns: "toast" }))
                setSettings("loading", false)
            });
            if (!processor) return;
            
            const { signed_url } = processor;

            // asure to get localStorage blob if thats the case
            const audioToSend = getRecord().audioChunks;
            
            const upload = await uploadToGCS(signed_url, audioToSend, mime).catch(() => {
                toast.error(t("error_sending_record", { ns: "toast" }))
                setSettings("loading", false)
            });

            if (!upload) return;

            await sendGCSUrl(id as string, question_id, signed_url).then(response => {
                if (!hasNextQuestion) return endExam();
                
                // reset audio url and chunks
                setRecord("audioURL", "");
                setRecord("audioChunks", []);
                setRecord("canStop", false);
                setRecord("seconds", MAX_RECORD_SECONDS);

                mutate(`${ENDPOINT_EXAMS}/${router.query.id}/questions`)
            }).catch(() => setSettings("loading", false));

            clearTimeout(hasTimeout.current);

            setSettings("loading", false);
        } catch (error) {
            toast.error(i18n?.t('error_send_record'));    
            clearTimeout(hasTimeout.current);   
            setSettings("loading", false);
            console.error(error)
        }
    }

    const endExam = () => {
        setExams("questionIndex", 0);
        setExams("exam", null);
        setExams("expanded", false);
        setRecord("audioURL", "");
        setRecord("audioChunks", []);
        setRecord("canStop", false);
        setRecord("seconds", MAX_RECORD_SECONDS);
        setExams("finished", true);
        setSettings("loading", false);
        clearTimeout(hasTimeout.current);
        router.push("/finish");
    }

    const clear = () => {
        setExams("expanded", false);
        setRecord("audioURL", "");
        setRecord("audioChunks", []);
        setRecord("canStop", false);
        setRecord("state", "inactive");
        setRecord("seconds", MAX_RECORD_SECONDS);
        setSettings("loading", false);
    }

    const isLoading = useCallback((button : IButton) => {
        switch (button.name) {
            case 'record':
                if (state === "recording" && !audioURL) return true;
                return false;
            case 'stop':
                return false;
            case 'next':
                return false;
            default:
                return false;
        }
    }, [state, audioURL]);

    const isDisabled = useCallback((button : IButton) => {
        switch (button.name) {
            case 'record':
                if (state === "recording") return true;
                if (audioURL) return true;
                return false;
            case 'stop':
                if (!canStop) return true;
                if (state === "recording") return false;
                return true;
            case 'next':
                if (state === "recording") return true;
                if (audioURL) return false;
                return true;
            default:
                return true;
        }
    }, [state, audioURL, canStop]);

    const getMessage = (button : IButton) => {
        if (!mediaRecorder || !mediaRecorder.current) return button.name;

        switch (button.name) {
            case 'record':
                if (mediaRecorder.current.state === "recording") return "recording_state";
            case 'stop':
                if (mediaRecorder.current.state === "recording") return "stop_recording_state";
            // case 'next':
            //     if (mediaRecorder.current.state === "recording") return "";
            default:
                return button.name;
        }
    }

    const getClasses = (button : IButton) => {
        const disabled = isDisabled(button);
        const baseClass = ['rounded-full border sm:border-gray-300 sm:shadow-lg flex items-center justify-center w-14 h-14 sm:w-[100px] sm:h-[100px]'];
        const disabledColor = 'bg-gray-300 sm:bg-gray-200';
        
        let customClass = [`${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`];

        switch (button.name) {
            case 'record':
                customClass.push(`w-20 h-20 md:w-[150px] md:h-[150px] ${!disabled ? 'bg-blue-500 sm:bg-gray-200 hover:bg-gray-200/80' : disabledColor}`);
                break;
            case 'stop':
                if (state === "recording" && canStop) customClass.push("bg-red-500 sm:bg-red-200 sm:hover:bg-red-200/80");
                customClass.push(`${!disabled ? 'sm:bg-gray-100 sm:hover:bg-gray-50' : disabledColor}`)
                break;
            case 'next':
                if (audioURL) customClass.push('bg-blue-500 sm:bg-blue-200 sm:hover:bg-blue-200/80');
                else customClass.push(`${!disabled ? 'sm:bg-gray-100 sm:hover:bg-gray-50' : disabledColor}`)
                break;
            default:
                break;
        }

        return baseClass.concat(customClass).join(" ")
    }   

    return (
        <>
            <div className="w-full h-full grid grid-cols-3 grid-rows-2 sm:grid-cols-3 sm:grid-rows-none justify-center justify-items-center items-center">
                {buttons.map((button : IButton, index: number) => (
                    <div key={index} className={`grid gap-2 justify-center min-w-[100px] max-w-[100px] md:min-w-[200px] md:max-w-[200px] col-span-1 items-stretch ${button.classes}`}>
                        <div className="relative justify-center flex -mb-1">
                            <Button 
                                action={button.action} 
                                icon={button.icon}
                                name={button.name}
                                disabled={isDisabled(button)}
                                classes={getClasses(button)}
                                size={button.size}
                                loading={isLoading(button)}
                            />
                            {isLoading(button) && <div className="absolute right-0 top-1/4">
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-300 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-400"></span>
                                </span>
                            </div>}
                        </div>
                        <span className="hidden md:flex w-full items-center justify-center break-all">
                            {t(getMessage(button), { ns: "exam" })}
                        </span>
                    </div>   
                ))}
            </div>
        </>
    )
}

export default Recorder;