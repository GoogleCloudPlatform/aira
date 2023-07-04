import { ICON_LANGUAGE } from "@/constants/icons";
import useIcon from "@/hooks/useIcon/useIcon";
import { useRouter } from "next/router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import Image from "next/image";

type TProps = {
    type?: string;
}

const Language : React.FC<TProps> = ({ type = "MENU" }) => {
    const [show, setShow] = useState<boolean>(false);

    const router = useRouter();
    const { t } = useTranslation();
    const { getIcon } = useIcon();
    const { locale, asPath, pathname, query } = router;

    const languages = [
        { name: "pt-BR", label: "pt-BR" },
        { name: "en-US", label: "en-US" },
        { name: "es-ES", label: "es-ES" },
    ];

    const renderFlag = (flag : string) => {
        if (!flag) return null;

        const src = `/assets/icons/${flag.split("-")[1]}.svg`;
        
        return (
            <>
                {/* <span className={`fi fis inline-block fi-br fi-circle`} /> */}
                <div className="h-6 w-6 relative">
                    <Image
                        src={src}
                        alt={flag}
                        fill
                        className="rounded-full"
                    />
                </div>
            </>
        );
    }

        

    return (
        <>
            <div className={`flex items-center sm:order-2 relative ${type === "MENU" ? '': ' bg-blue-500'} rounded-lg`}>
                <button 
                    type="button"
                    data-dropdown-toggle="language-dropdown-menu" 
                    className="inline-flex items-center font-medium justify-center px-4 py-2 text-sm text-white rounded-lg cursor-pointer bg-white/10 hover:bg-white/20"
                    onMouseEnter={() => setShow(true)}
                    onClick={() => setShow(!show)}
                >
                    <div className="w-5 h-5">
                        {getIcon({ icon: ICON_LANGUAGE, classes: "" })}
                    </div>
                </button>
                {show ?
                    <div 
                        id="language-dropdown-menu"
                        className={`z-50 my-4 text-sm list-none ${type === "MENU" ? 'bg-blue-800/90 sm:bg-blue-600': 'bg-blue-500 '}  rounded-lg shadow absolute 
                                    ${type === "MENU" ? '-left-16' : '-left-[80px]'}  flex flex-col
                                    bottom-8 
                                    ${type === "MENU" ? 'sm:bottom-auto sm:left-[75px]': 'sm:-left-[80px]'}`}
                        onMouseLeave={() => setShow(false)}
                    >
                        {languages.map(language => {
                            return (
                                <button
                                    key={language.name}
                                    className={`px-4 py-2 flex gap-3 ${
                                        locale === language.name ? 'bg-white/5 sm:bg-white/20 ' : 'hover:bg-white/10'
                                    }`}
                                    onClick={() => router.push({ pathname, query }, asPath, { locale: language.name })}
                                >
                                    <div className="flex flex-shrink">
                                        {renderFlag(language.name)}
                                    </div>
                                    <span className="flex flex-grow text-white">
                                        {t(language.label, { ns: "common" })}
                                    </span>
                                </button>
                            )
                        })}
                    </div>
                    :
                    null
                }
            </div>
        </>
    );
}

export default Language;