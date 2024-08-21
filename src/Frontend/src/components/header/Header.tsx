'use client';

import React from 'react'
import { ISettingsStore } from '@/interfaces/store';
import { useSettingsStore } from '@/store/settings';
import { Sidebar } from '@/components';
import { MenuIcon } from 'lucide-react';

const Header : React.FC = () => {
    const { setSettings }: ISettingsStore = useSettingsStore();

    const handleMenuClick = ()=>{
        setSettings('menu', true)
    }

    return (
        <>
            <div className='flex md:hidden bg-primary dark:bg-darkPrimary w-full p-4 justify-end items-center'>
                <button className='w-7 h-7 flex items-center' onClick={handleMenuClick}>
                    <MenuIcon />
                </button>
            </div>

            <Sidebar />
        </>
    )
}

export default Header;
