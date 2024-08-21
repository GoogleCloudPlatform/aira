'use client'

import useTheme from '@/hooks/useTheme';
import React from 'react'
import { MoonIcon, SunIcon } from 'lucide-react';

const ThemeSwitch : React.FC = () => {  
    const { ToggleTheme } = useTheme();

    return (
        <div className='flex items-center gap-2'>
            <SunIcon size={20} className='text-white'/>
            <ToggleTheme/>
            <MoonIcon size={20} className='text-white'/>
        </div>
    )
}

export default ThemeSwitch;