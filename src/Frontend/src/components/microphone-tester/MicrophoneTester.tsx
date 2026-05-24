import { MICROPHONE_DIALOG_TIPS } from "@/constants/exams";
import { ICON_PAUSE, ICON_PLAY } from "@/constants/icons";
import { STEP_EXAM_MIC_TESTER } from "@/constants/tour";
import useIcon from "@/hooks/useIcon";
import { LucideInfo, PauseIcon, PlayIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRef, useState, useEffect } from "react";
import { toast } from "react-toastify";

const MicrophoneTester: React.FC = () => {
    const { getIcon } = useIcon();
    const recordedChunks = useRef<Blob[]>([]);
    const t = useTranslations();
    const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
    const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
    const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const animationFrameIdRef = useRef<number | null>(null);

    useEffect(() => {
        return () => {
            stopRecording();
        };
    }, []);

    useEffect(() => {
        if (!analyser) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const canvasCtx = canvas.getContext('2d');
        if (!canvasCtx) return;

        // Set matching resolution internally
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;

        drawCanvas(analyser, canvasCtx, canvas);
    }, [analyser]);

    const checkMicrophonePermissions = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            return stream;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            return null;
        }
    };

    const drawCanvas = (analyserNode: AnalyserNode, canvasCtx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
        const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
        analyserNode.getByteTimeDomainData(dataArray);

        // Periodic diagnostic logging to trace Web Audio state in browser console
        if (Math.random() < 0.01) {
            console.log(`[MicrophoneTester Debug] state: ${analyserNode.context.state}, sampleRate: ${analyserNode.context.sampleRate}, data: [${Array.from(dataArray.slice(0, 10)).join(', ')}]`);
        }

        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
        canvasCtx.lineWidth = 2;
        
        // line style
        const gradient = canvasCtx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, 'red');
        gradient.addColorStop(0.5, 'green');
        gradient.addColorStop(1, 'blue');
        canvasCtx.strokeStyle = gradient;

        canvasCtx.beginPath();
        const sliceWidth = (canvas.width * 1.0) / dataArray.length;
        let x = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * canvas.height) / 2;
            if (i === 0) {
                canvasCtx.moveTo(x, y);
            } else {
                canvasCtx.lineTo(x, y);
            }
            x += sliceWidth;
        }
        canvasCtx.lineTo(canvas.width, canvas.height / 2);
        canvasCtx.stroke();
       
        animationFrameIdRef.current = requestAnimationFrame(() => drawCanvas(analyserNode, canvasCtx, canvas));
    };

    const handleRecording = async () => {
        if (isRecording) {
            // Stop the recording if already recording
            stopRecording();
            setIsRecording(false);
            return;
        }

        // Reset the recorded chunks at the beginning of recording
        recordedChunks.current = [];

        // Create AudioContext synchronously inside user gesture to avoid suspension
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();

        const microphoneStream = await checkMicrophonePermissions();

        if (microphoneStream) {
            console.log('[MicrophoneTester Debug] Stream Tracks:', {
                id: microphoneStream.id,
                active: microphoneStream.active,
                tracks: microphoneStream.getAudioTracks().map(t => ({
                    id: t.id,
                    kind: t.kind,
                    label: t.label,
                    enabled: t.enabled,
                    muted: t.muted,
                    readyState: t.readyState,
                }))
            });
        }

        if (!microphoneStream) {
            audioCtx.close();
            return toast.warn(t('toast.warnings.exam.warning_microphone_permission'));
        }

        // Explicitly resume AudioContext if it starts suspended
        if (audioCtx.state === 'suspended') {
            await audioCtx.resume();
        }

        const analyserNode = audioCtx.createAnalyser();
        const source = audioCtx.createMediaStreamSource(microphoneStream);
        source.connect(analyserNode);

        // Connect to silent GainNode terminating at destination to guarantee browser graph processing
        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0;
        analyserNode.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        setAudioContext(audioCtx);
        audioContextRef.current = audioCtx;
        setAnalyser(analyserNode);
        setMediaStream(microphoneStream);
        mediaStreamRef.current = microphoneStream;

        const mediaRecorder = new MediaRecorder(microphoneStream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event: BlobEvent) => {
            if (event.data.size > 0) {
                recordedChunks.current.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(recordedChunks.current, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        };

        mediaRecorder.start();
        setIsRecording(true);
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        if (mediaStreamRef.current && typeof mediaStreamRef.current.getTracks === 'function') {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
            mediaStreamRef.current = null;
        }
        if (animationFrameIdRef.current !== null) {
            cancelAnimationFrame(animationFrameIdRef.current);
            animationFrameIdRef.current = null;
        }

        setAnalyser(null);
        setAudioContext(null);
        setMediaStream(null);
    };

    return (
        <>
            <button 
                data-step={STEP_EXAM_MIC_TESTER}
                onClick={() => handleRecording()} 
                className={`w-fit justify-self-center border-2 border-border dark:border-darkBorder shadow-sm flex gap-1 p-2 bg-secondary dark:bg-darkSecondary/70 dark:hover:bg-darkSecondary hover:bg-border rounded-full cursor-pointer items-center max-h-12`}
            >
                { isRecording ? <PauseIcon size={20} className='text-red-500 fill-red-500' /> : <PlayIcon size={20} className='text-green-500 fill-green-500' /> }
                <div className="h-full flex items-center justify-center w-[110px]">
                    <span 
                        style={{ display: !isRecording ? 'flex' : 'none'}}
                        className="text-xs h-full flex items-center w-full justify-center text-black dark:text-white font-bold"
                    >
                        {t("exam.buttons.microphone_tester")}
                    </span>
                        
                    <canvas
                        ref={canvasRef}
                        style={{ display: isRecording ? 'block' : 'none' }}
                        className="w-full h-full"
                    />
                </div>
            </button>
        </>
    )
}

const MicrophoneTesterWrapper : React.FC = () => {
    const t = useTranslations('exam');

    return (
        <>
            <section className="grid gap-4 py-4 items-center justify-center">
                <ul className='flex flex-col gap-3 list-decimal px-5 mt-2 text-sm'>
                    {MICROPHONE_DIALOG_TIPS.map((tip, index) => {
                        return <li key={index} className="text-black dark:text-white">{t(`tips.${tip.label}`)}</li>;
                    })}
                </ul>

                <MicrophoneTester />

                <div className='font-bold relative flex gap-3 items-center'>
                    <div
                        className='w-10 h-10 flex items-center justify-center cursor-pointer text-black dark:text-white'
                    >
                        <LucideInfo className="w-5 h-5 text-black dark:text-white" />
                    </div>
                    <span
                        className='cursor-pointer hover:underline text-black dark:text-white'
                    >
                        {t('tips.tip_tour')}
                    </span>
                </div>
            </section>

        </>
    )
}

export { MicrophoneTester, MicrophoneTesterWrapper };
