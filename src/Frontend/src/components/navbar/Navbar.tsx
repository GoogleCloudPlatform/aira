import { ICON_BARS_3 } from "@/constants/icons";
import useIcon from "@/hooks/useIcon/useIcon";
import { ISettingsStore } from "@/interfaces/store";
import { useSettingsStore } from "@/store/settings";
import Image from "next/image";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";
import Menu from "../menu/Menu";
import { useEffect } from "react";

const Navbar : React.FC = () => {
    const router = useRouter();
    const { asPath, query, pathname } = router;

    const { t } = useTranslation();
    const { menu, setSettings } : ISettingsStore = useSettingsStore();
    const { getIcon } = useIcon();

    const getPageName = () => {
        const { id, slug } = query;
        let key = asPath;
        if (id) key = pathname
        return t(key, { ns: "routes" });
    }

    useEffect(() => {
        setSettings("menu", false);
    }, [setSettings])

    return (
        <>
            {menu ? <Menu /> : null}
            <nav className="w-full h-full bg-blue-600 relative">
                <div className='w-full h-full flex justify-between items-center px-2 md:px-5'>
                    <div className='flex gap-2 md:gap-5 h-full items-center'>
                        <div className='ml-2 cursor-pointer' onClick={() => setSettings("menu", true)}>
                            <div className="w-8 h-8">
                                {getIcon({ icon: ICON_BARS_3, classes: "text-white" })}
                            </div>
                        </div>
                        <div className='logo mr-3 sm:mr-5 md:ml-0 p-1 absolute right-0'>
                            <div className="relative sm:w-[100px] sm:h-[60px] h-[50px] w-[90px]">
                                <Image
                                    src="/assets/images/logo.png" 
                                    alt="logo" 
                                    fill
                                    sizes="(max-width: 768px) 100vw"
                                    priority
                                />
                            </div>
                        </div>
                        <div className="flex gap-8 sm:ml-4 ml-1 text-xl sm:text-2xl text-white">
                            <h1>{getPageName()}</h1>
                        </div>
                    </div>
                </div>
            </nav>
        </>
    )
}

export default Navbar;