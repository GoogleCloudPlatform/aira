import React from 'react'
import { useTranslations } from 'next-intl';
import { useRBAC } from '@/context/rbac';
import { SCOPE_ADMIN, SCOPE_USER_IMPERSONATE } from '@/constants/rbac';

const Permissions : React.FC = () => {
    const t = useTranslations('home');
    const { hasScopePermission } = useRBAC();

    const getPermissions = () : Array<string> => {
        if (hasScopePermission([SCOPE_ADMIN])) {
            return ['permission__actions','permission__reports','permission__docs'];
        }

        if (hasScopePermission([SCOPE_USER_IMPERSONATE])) {
            return [
                'permission__user_groups',
                'permission__studants_groups',
                'permission__apply_exams',
                'permission__analyze_performance',
                'permission__url',
            ];
        }

        return ['permission__exams'];
    }
    
    return (
        <ul className='text-sm text-black/80 dark:text-white/50 list-disc ml-6'>
            {getPermissions().map((permission, i) => {
                return (
                    <li key={i}>
                        {t(`permissions.${permission}`)}
                    </li>
                )
            })}
        </ul>
    );
}

export default Permissions