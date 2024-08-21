'use client'

import React, { useEffect, useState } from 'react';
import { RBACWrapper, useRBAC } from '@/context/rbac';
import { SCOPE_ADMIN, SCOPE_USER, SCOPE_USER_IMPERSONATE } from '@/constants/rbac';
import { useTranslations } from 'next-intl';
import Permissions from './Permissions';
import ExamsTable from './ExamsTable';
import { getProfile } from '@/services/user';
import { useQuery } from '@tanstack/react-query';
import SkeletonHome from '../skeletons/SkeletonHome';
import { Card, CardGroups, CardOrganization, CardUsers } from './Cards';
import { isEmpty } from 'lodash';
import { costumer } from '@/app/[locale]/setup';

const Home: React.FC<HomeProps> = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const { hasScopePermission } = useRBAC();

    const { data: profile } = useQuery({ 
        queryKey: ['profile'], 
        queryFn: () => getProfile(),
        retryOnMount: false, retry: false,
        enabled: mounted
    })

    const t = useTranslations('home');

    const getRoleType = () => {
        if (hasScopePermission([SCOPE_ADMIN])) return t('profiles.profile__user__admin');
        if (hasScopePermission([SCOPE_USER_IMPERSONATE])) { 
            if (costumer === 'SABER')  return t('profiles.profile__user__impersonate_saber')

            return t('profiles.profile__user__impersonate')
        };
        if (hasScopePermission([SCOPE_USER])) return t('profiles.profile__user__student');
        return 'profile_user';
    }
   
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        };
    }, [setMounted]);

    if (!profile) return <SkeletonHome />;
    if (!mounted) return null;

    return (
        <RBACWrapper requiredScopes={[SCOPE_ADMIN, SCOPE_USER_IMPERSONATE, SCOPE_USER]}>
            <article className='w-full h-full p-4 lg:p-12 overflow-y-auto'>
                <section className='bg-gradient-to-r rounded-xl flex items-center gap-20 relative'>
                    <div>
                        <h1 className='font-semibold text-2xl md:text-3xl text-primary dark:text-white mb-1'>
                            {t('messages.hello_message')}, {profile?.name}!
                        </h1>
                        <h2 className='text-black/80 dark:text-white/80 text-base md:text-xl'>
                            {costumer === 'SABER' ? t('messages.welcome__message_saber') : t('messages.welcome__message')}
                        </h2>
                    </div>
                </section>

                <section className='w-full flex justify-center mt-8'>
                    <div className='px-4 py-6 border border-border dark:border-darkBorder rounded-md bg-black/5 dark:bg-white/10 border-l-4 border-l-primary dark:border-l-darkPrimary-foreground shadow-md w-full'>
                        <h3 className='text-black/80 dark:text-white/50 text-sm md:text-sm mb-4'>
                            {costumer === 'SABER' ? t('messages.saber_message') : t('messages.lia_message')}
                        </h3>
                        <div className='text-sm text-black/80 dark:text-white/50 flex flex-col mb-1'>
                            <p className='space-x-1'>
                                <span>{t('profiles.profile__type')}</span>
                                <b className='text-primary dark:text-white'>{getRoleType()}.</b>
                            </p>
                            <span>{t('permissions.view_permissions')}</span>
                        </div>
                        
                        <Permissions />
                    </div>
                </section>

                <section className='flex flex-col sm:flex-row w-full gap-4 my-8'>
                    {!isEmpty(profile.organizations) && !isEmpty(profile.groups) ? 
                        <>
                            <Card label="group" total={profile.groups.length} route={'/groups'} />
                        </>
                        :
                        <>
                            <CardOrganization />
                            <CardGroups />
                            <CardUsers />
                        </>
                    }
                </section>

                <section>
                    <ExamsTable />
                </section>

            </article>
        </RBACWrapper>
    );
};

export default Home;