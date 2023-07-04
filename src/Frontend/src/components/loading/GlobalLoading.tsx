import { ANIMATION_SPIN } from "@/constants/animation";
import { useSettingsStore } from "@/store/settings";
import { Loading } from "@/components";
import { useEffect, useState } from "react";


const GlobalLoading : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);

    const { loading, setSettings } = useSettingsStore();

    useEffect(() => {
        setMounted(true);
        return () => {
            setSettings("loading", false);
            setMounted(false);
        }
    }, [setSettings]);
    
    if (!mounted || !loading) return null;

    return (
        <>            
            <div className="absolute top-0 w-full h-screen z-50 bg-zinc-500 opacity-70 overflow-hidden">
                <div className="flex items-center justify-center h-full text-white">
                    <Loading animation={ANIMATION_SPIN} size={12} />
                </div>
            </div>
        </>
    )
}

export default GlobalLoading;