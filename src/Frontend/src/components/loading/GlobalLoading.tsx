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