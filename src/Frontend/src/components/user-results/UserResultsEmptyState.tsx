import { Link } from '@/router/link/Link'
import { useTranslations } from 'next-intl';
import React from 'react'

const UserResultsEmptyState = () => {

    const t  = useTranslations('results.emptyState');

    return ( 
        <div className='w-full h-full text-black dark:text-white flex flex-col justify-center items-center'>
            <h2 className='text-xl font-semibold'>{t('title')}</h2>
            <p className='text-gray-500'>{t('message')}</p>
            <Link href="/exams" className='bg-primary px-6 py-2 text-white rounded-md hover:bg-primary/90 transition-all mt-4'>
                {t('linkText')}
            </Link>
        </div>
    )
}

export default UserResultsEmptyState
