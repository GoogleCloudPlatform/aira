'use client'
import { useParams, usePathname, useRouter } from 'next/navigation';
import { useRef } from 'react';
import Image from 'next/image';
import { ISettingsStore } from '@/interfaces/store';
import { useSettingsStore } from '@/store/settings';
import { useTranslations } from 'next-intl';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Button } from '../ui/button';
import { LanguagesIcon } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';

type TProps = {
  type?: string;
};

const Language: React.FC<TProps> = ({ type = 'MENU' }) => {
    const { locale } = useParams();
    const pathname = usePathname();
    const t = useTranslations();
    const { menu } : ISettingsStore = useSettingsStore();
    const router = useRouter();
    
    const languages = [
        { name: 'pt-BR', label: 'pt-BR' },
        { name: 'en-US', label: 'en-US' },
        { name: 'es-ES', label: 'es-ES' },
    ];

    const renderFlag = (flag: string) => {
        if (!flag) return null;

        const src = `/assets/icons/${flag.split('-')[1]}.svg`;

        return (
            <>
                <div className='h-5 w-5 relative'>
                    <Image src={src} alt={flag} fill className='rounded-full' />
                </div>
            </>
        );
    };

    const changeLanguage = (language: string) => {
        const goTo = pathname.replace(locale as string, language) ;
        router.push(goTo);
    }

    return (
        <>
            {type === 'MENU' ? (
                <Collapsible className={`${menu ? 'w-full flex flex-col justify-center ' : ''}`}>
                    <CollapsibleTrigger asChild>
                        <Button className={`w-full ${!menu ? ' md:justify-center md:p-1' : ''} flex items-center justify-start px-2 gap-4 text-white hover:bg-white/5 rounded-lg mt-2 bg-transparent dark:bg-transparent dark:hover:bg-white/5 shadow-none h-10`}>
                            <div className='w-6 h-6'>
                                <LanguagesIcon /> 
                            </div>
                            <span className={`text-xs font-normal ${!menu ? 'md:hidden' : ''}`}>
                                {t(`sidebar.language`)}
                            </span>  
                        </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className='flex flex-col items-center gap-1'>
                        {languages.map((language) => {
                            return (
                                <Button  key={language.name} className={`bg-transparent dark:bg-transparent shadow-none ${!menu ? 'md:justify-center' : 'ml-1'} w-full flex items-center justify-start gap-4 text-white hover:bg-white/5 dark:hover:bg-white/5 px-2 rounded-lg first-of-type:mt-1 h-10`} onClick={() => changeLanguage(language.name)}>
                                    {renderFlag(language.name)}
                                    <span className={`text-xs font-normal ${!menu ? 'md:hidden' : ''}`}>
                                        {t(`sidebar.languages.${language.label}`)}
                                    </span>
                                </Button>
                            );
                        })}
                    </CollapsibleContent>
                </Collapsible>
            ) : (
                <Popover>
                    <PopoverTrigger asChild>
                        <Button className='bg-background dark:bg-darkBackground text-primary dark:text-white hover:bg-background/80 dark:hover:bg-darkBackground/80'>  
                            <LanguagesIcon />                              
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className='w-max flex flex-col gap-2 mr-5'>
                        {languages.map((language) => {
                            return (
                                <Button variant={'outline'} key={language.name} className='justify-start w-full gap-2' onClick={() => changeLanguage(language.name)}>
                                    {renderFlag(language.name)}
                                    <span>
                                        {t(`sidebar.languages.${language.label}`)}
                                    </span>
                                </Button>
                            );
                        })}
                    </PopoverContent>
                </Popover> 
            )}
        </>
    );
};

export default Language;
