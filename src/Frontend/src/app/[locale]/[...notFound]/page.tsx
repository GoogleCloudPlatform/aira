'use client'

import { useTranslations } from 'next-intl'
import { useTheme } from 'next-themes'
import Image from 'next/image'
import Link from 'next/link'
import { signinLogoDark, signinLogoLight, costumer } from '../setup'
 
export default function NotFound() {
    const t = useTranslations('toast.errors.page_not_found')
    const { theme } = useTheme()
    const logo = theme ==='dark' ? costumer === 'SABER' ? signinLogoDark : signinLogoLight : signinLogoDark

    return (
        <main className='w-full h-screen max-h-screen flex flex-col gap-2 items-center justify-center bg-primary dark:bg-darkPrimary'>
            <Image
                src={logo}
                alt='logo'
                width={200}
                height={200}
                className='w-[250px] h-auto mb-5'
                blurDataURL={logo}
                priority
            />
            <h2 className='text-white dark:text-darkPrimary-foreground font-extrabold text-[150px] md:text-[200px] leading-[150px] md:leading-[200px]'>404</h2>
            <p className='text-white md:text-xl'>{t('page_not_found')}</p>
            <Link href="/home" className='text-white text-sm bg-primary-foreground dark:bg-darkPrimary-foreground py-2 px-4 rounded cursor-pointer hover:bg-primary-foreground/60 dark:hover:bg-darkPrimary-foreground/60 transition-all mt-2'>{t('button_back_home')}</Link>
        </main>
    )
}