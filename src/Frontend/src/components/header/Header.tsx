import Image from "next/image";
import { useTranslation } from "react-i18next";


const Header : React.FC = () => {
    const { t } = useTranslation();
    

    return (
        <>
            <nav className="w-full h-full bg-blue-600">
                <div className='w-full h-full flex justify-between items-center px-2 md:px-10'>
                    <div className='flex gap-2 md:gap-5 h-full items-center'>
                        <div className='logo mr-2 md:ml-0 p-1 absolute right-0 sm:relative'>
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
                        <div className="hidden md:flex md:gap-8 md:ml-4 text-2xl text-white">
                            <h1>{t("title", { ns: "common" })}</h1>
                        </div>
                    </div>
                </div>
            </nav>
        </>
    )
}

export default Header;