'use client'

import { useEffect, useState } from 'react';
import Image from 'next/image';
import useIcon from '@/hooks/useIcon';
import { ISettingsStore } from '@/interfaces/store';
import { useSettingsStore } from '@/store/settings';
import { ICON_BARS_3, ICON_CHEVRON_LEFT, ICON_X_MARK } from '@/constants/icons';
import { sidebarLogoDark, sidebarLogoLight, sidebarLogoSize } from '@/app/[locale]/setup'

import Menu from '../menu/Menu';
import useTheme from '@/hooks/useTheme';

const Sidebar: React.FC = () => {
    const [screenWidth, setScreenWidth] = useState<number>(window.innerWidth);
    const { menu, setSettings }: ISettingsStore = useSettingsStore();
    const { getIcon } = useIcon();

    const { theme } = useTheme()
    const logo = theme ==='dark' ? sidebarLogoDark : sidebarLogoLight

    const handleMenuClick = () => {
        setSettings('menu', !menu)
    }

    useEffect(() => {
        if (screenWidth < 768) {
            setSettings('menu', false);
        }
    }, [setSettings, screenWidth]);

    useEffect(() => {
        const handleResize = () => {
            setScreenWidth(window.innerWidth);
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    const mobileSidebar = () => {
        return (
            <>
                <div className={`p-4 bg-primary dark:bg-darkPrimary fixed h-full top-0 left-0 z-50 flex flex-col  ${menu ? 'w-full': 'hidden'} overflow-y-auto`}>
                    <div className={`flex items-center justify-between mb-6`}>
                        <Image
                            src={logo}
                            alt='Governo do Paraná'
                            width={0}
                            height={0}
                            sizes='100vw'
                            className='w-[120px]'
                            priority={menu}
                            placeholder="blur"
                            blurDataURL={'./public/assets/images/logo.png'}
                        />
                        <button onClick={handleMenuClick} className='w-6 h-6'>
                            {getIcon({ icon: ICON_X_MARK, classes: 'text-white' })}
                        </button>
                    </div>
            
                    <div className={`hidden items-center justify-center mb-6`}>
                        <button onClick={handleMenuClick} className='w-7 h-7'>
                            {getIcon({ icon: ICON_BARS_3, classes: 'text-white' })}
                        </button>
                    </div>
    
                    <div className='flex-1 flex'>
                        <Menu />
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            {screenWidth >= 768 ? (
                <aside className={`p-4 bg-primary dark:bg-darkPrimary min-h-screen max-h-screen flex flex-col ${menu ? 'sidebar-open': 'sidebar-close'} overflow-y-auto shadow-md shadow-black/20`}>
                    
                    <div className={`${menu ? 'flex': 'flex md:hidden'} items-center justify-between mt-6 mb-8 h-[40px]`}>
                        <Image
                            src={logo}
                            alt='logo'
                            width={120}
                            height={35}
                            sizes='100vw'
                            className={sidebarLogoSize}
                            priority={menu}
                            placeholder="blur"
                            blurDataURL={logo}
                        />
                        <button onClick={handleMenuClick} className='w-5 h-5'>
                            {getIcon({ icon: ICON_CHEVRON_LEFT, classes: 'text-white' })}
                        </button>
                    </div>
                
                    <div className={`${menu ? 'hidden': 'hidden md:flex'} items-center justify-center mt-6 mb-8 h-[40px]`}>
                        <button onClick={handleMenuClick} className='w-10 h-10 p-1'>
                            {getIcon({ icon: ICON_BARS_3, classes: 'text-white' })}
                        </button>
                    </div>
                 
                    <nav className='flex flex-grow'>
                        <Menu />
                    </nav>
                </aside>
            )
                :
                mobileSidebar()
            } 
        </>
    );
};
            
export default Sidebar;
            