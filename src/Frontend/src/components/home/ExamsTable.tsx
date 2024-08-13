'use client'

import React, { useEffect } from 'react';
import { getFormattedDate } from '@/utils';
import { IExam } from '@/interfaces/exam';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../ui/table';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useRBAC } from '@/context/rbac';
import { SCOPE_ADMIN, SCOPE_USER } from '@/constants/rbac';
import { useQuery } from '@tanstack/react-query';
import { getExams } from '@/services/exam';
import { getExamsByUserId } from '@/services/user';
import { useAuth } from '@/context/auth';
import Link from 'next/link';
import { IPaginationStore } from '@/interfaces/store';
import { usePaginationStore } from '@/store/pagination';
import SkeletonHomeTable from '../skeletons/SkeletonHomeTable';


const ExamsTable: React.FC = () => {
    const t = useTranslations('home.home_table');
    const router = useRouter();
    const { hasScopePermission } = useRBAC();
    const { user } = useAuth();
    const { setPagination } : IPaginationStore = usePaginationStore();

    const isStudent = hasScopePermission([SCOPE_USER]);

    const { data, isLoading } = useQuery({ 
        queryKey: ['exams'], 
        queryFn: () => !isStudent ? getExams() : getExamsByUserId(user ? user.user_id : ''),
        retryOnMount: false, retry: false,
    });
    
    useEffect(()=>{
        setPagination("page", 1);
        setPagination("page_size", 5);
    },[router,setPagination])

    if (isLoading) return <SkeletonHomeTable/>;
    if (!data) return null;

    const goToExam = (exam_id: string) => {
        // @TODO - open a quick selection of students and redirect to <user_id>/<exam_id>
        if (isStudent) {
            router.push(`/exams/${exam_id}`);
        }
    }

    return (
        <section>
            <div className='flex items-center justify-between mb-1'>
                <h3 className='font-bold text-primary dark:text-white'>
                    {t('title')}
                </h3>
                <Link
                    href={hasScopePermission([SCOPE_ADMIN]) ? '/admin/exams' : '/users/exams'}
                    className='text-xs text-black/80 dark:text-white/80'
                >
                    {t('button')}
                </Link>
            </div>

            <Table className='rounded-md overflow-hidden'>
                <TableHeader className='dark:bg-darkPrimary bg-primary'>
                    <TableRow>
                        <TableHead className='text-white'>
                            {t('name')}
                        </TableHead>
                        <TableHead className='text-white w-[150px]'>
                            {t('grade')}
                        </TableHead>
                        <TableHead className='text-white w-[150px]'>
                            {t('start_date')}
                        </TableHead>
                        <TableHead className='text-white w-[150px]'>
                            {t('end_date')}
                        </TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody className='bg-gray-100 dark:bg-darkPrimary/50'>
                    {data.items.map((exam: IExam) => (
                        <TableRow key={exam.id} onClick={() => goToExam(exam.id)} className={`${isStudent && 'cursor-pointer'}`}>
                            <TableCell className='font-medium text-black dark:text-white'>{exam.name}</TableCell>
                            <TableCell className='font-medium text-black dark:text-white'>{exam.grade}</TableCell>
                            <TableCell className='text-black dark:text-white'>
                                {getFormattedDate('pt-BR' as string, new Date(exam.start_date))}
                            </TableCell>
                            <TableCell className='text-black dark:text-white'>
                                {getFormattedDate('pt-BR' as string, new Date(exam.end_date))}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </section>
    );
};

export default ExamsTable;
