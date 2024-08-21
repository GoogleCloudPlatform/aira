import { ICON_ARROW_LEFT_ON_RECTANGLE, ICON_ELLIPSIS_VERTICAL, ICON_USER_CIRCLE } from '@/constants/icons';
import { useAuth } from '@/context/auth';
import useClickOutside from '@/hooks/useClickOutside';
import useIcon from '@/hooks/useIcon';
import { useRef, useState } from 'react';
import { ISettingsStore } from '@/interfaces/store';
import { useSettingsStore } from '@/store/settings';
import { useTranslations } from 'next-intl';
import Language from '../language/Language';
import useTheme from '@/hooks/useTheme';
import { LucideMoon, LucideSun } from 'lucide-react';

const Profile: React.FC = () => {
    const profileRef = useRef<HTMLDivElement>(null);
    const [show, setShow] = useState<boolean>(false);
    
    const t = useTranslations('sidebar');
    const { menu }: ISettingsStore = useSettingsStore();
    const { getIcon } = useIcon();
    const { user, signOut } = useAuth();
    const { ButtonTheme, theme, toggleTheme } = useTheme();

    const toggleShow = () => setShow(prev => !prev);

    useClickOutside(profileRef, toggleShow);

    return (
        <>
            {show && (
                <div ref={profileRef} className={`${!menu && 'md:items-center md:px-0'} w-full mb-2 flex flex-col items-start justify-center bg-white/5 rounded-lg p-2 text-xs`}>
                    <button onClick={toggleTheme} className={`${menu ? 'w-full' : 'w-full md:w-max md:justify-center md:p-1'} flex items-center justify-start gap-4 text-white hover:bg-white/5 p-2 rounded-lg`}>
                        <div className='w-6 h-6'>
                            {theme !== "dark" ? <LucideMoon /> : <LucideSun />}
                        </div>
                        <span className={`${menu ? 'md:block' : 'md:hidden'} `}>
                            {t('theme')}
                        </span>
                    </button>
                    <Language />
                    <button onClick={signOut} className={`${menu ? 'w-full' : 'w-full md:w-max md:justify-center md:p-1'} flex items-center justify-start gap-4 mt-2 text-white hover:bg-white/5 p-2 rounded-lg`}>
                        <div className='w-6 h-6 '>
                            {getIcon({
                                icon: ICON_ARROW_LEFT_ON_RECTANGLE
                            })}
                        </div>
                        <span className={`${menu ? 'md:block' : 'md:hidden'} `}>{t('exit')}</span>
                    </button>
                </div>
            )}
        
            <div className='w-full flex items-center justify-between p-2 rounded-lg text-white text-nowrap' >
                <div className='flex items-center gap-2'>
                    <button onClick={toggleShow} className={`relative w-8 h-8 rounded-full ${!menu ? 'hover:bg-white/5' : ''} cursor-pointer`}>
                        {getIcon({ icon: ICON_USER_CIRCLE, classes: '' })}
                    </button>
                    <span className={`${menu ? 'md:block cursor-default' : 'md:hidden'} text-sm`}>
                        {user ? user.user_name : ''}
                    </span>
                </div>
                <button onClick={toggleShow} className={`${show ? 'bg-white/5' : ''} cursor-pointer w-8 h-8 hover:bg-white/5 p-1 rounded-lg ${menu ? 'md:block' : 'md:hidden'}`}>
                    {getIcon({ icon: ICON_ELLIPSIS_VERTICAL, classes: '' })}
                </button>
            </div>
        </>
    );
};

export default Profile;
