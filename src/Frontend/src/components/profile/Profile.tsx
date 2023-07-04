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
import { ICON_ARROW_LEFT_ON_RECTANGLE, ICON_ELLIPSIS_VERTICAL, ICON_USER, ICON_USER_CIRCLE } from "@/constants/icons";
import { useAuth } from "@/context/auth";
import useClickOutside from "@/hooks/useClickOutside/useClickOutside";
import useIcon from "@/hooks/useIcon/useIcon";
import { useRouter } from "next/router";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Language from "../language/Language";

const Profile : React.FC = () => {
    const profileRef = useRef<HTMLDivElement>(null);
    const [show, setShow] = useState<boolean>(false);

    const router = useRouter();
    const { t } = useTranslation();
    const { getIcon } = useIcon();
    const { user } = useAuth();
    
    const toggleShow = () => setShow(!show);
    
    useClickOutside(profileRef, toggleShow);

    return (
        <>
            <div className="flex justify-end items-center gap-4 w-full h-full p-2">
                <div className="w-full h-full px-2" id="menu-button" aria-expanded="true" aria-haspopup="true">
                    <div className="w-full h-full flex text-white items-center justify-between">
                        <div className="w-full h-full flex items-center gap-2">
                            <div className="relative w-10 h-10 sm:w-10 sm:h-10 cursor-pointer rounded-full">
                                {getIcon({ icon: ICON_USER_CIRCLE, classes: "" })}
                            </div>
                            <div className="text-sm">
                                {user ? user?.email : ""}
                            </div>
                        </div>
                        <button className={`p-1 rounded-full hover:bg-white/5 ${show ? 'bg-white/5': ''}`} onClick={() => toggleShow()}>
                            <div className="w-6 h-6 sm:w-7 sm:h-7">
                                {getIcon({ icon: ICON_ELLIPSIS_VERTICAL, classes: "" })}
                            </div>
                        </button>
                    </div>
                </div>

                {show && (
                    <div className="absolute bottom-14 sm:bottom-2 sm:-right-[260px] z-40 rounded-lg bg-blue-800/90 sm:bg-blue-600">
                        <div
                            ref={profileRef} 
                            role="menu" 
                            aria-orientation="vertical" 
                            aria-labelledby="menu-button"
                            className="h-full flex flex-col items-center text-white rounded-lg w-64 divide-y divide-white/20"
                        >
                            <div className={`py-1 hover:bg-white/5 sm:hover:bg-white/20 w-full h-[48px] flex items-center rounded-t-lg`}> 
                                <div className="flex items-center justify-between text-sm w-full h-full px-4 py-2 ">
                                    <div className="cursor-default">
                                        {t("language", { ns: "common" })}
                                    </div>
                                    <div>
                                        <Language />
                                    </div>
                                </div>
                            </div>
                            <div className="py-1 hover:bg-white/20 w-full h-[48px] cursor-pointer" onClick={() => router.push("/")}> 
                                <div className="flex items-center justify-between px-4 py-2 text-sm">
                                    <div className="flex items-center gap-3 text-white">
                                        <div className="w-6 h-6">
                                            {getIcon({ icon: ICON_ARROW_LEFT_ON_RECTANGLE, classes: "" })}
                                        </div>
                                        <div>
                                            {t("exit", { ns: "routes" })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                
            </div>
        </>
    )
}

export default Profile;