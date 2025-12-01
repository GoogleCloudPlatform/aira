'use client';

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { isEmpty } from "lodash";
import { usePaginationStore } from "@/store/pagination";
import { IPaginationStore } from "@/interfaces/store";
import { getExamsResultsByUserId, getUserById, } from "@/services/user";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { IExam } from "@/interfaces/exam";
import { toast } from "react-toastify";
import ExamResult from "./ExamResult";
import SkeletonResults from "../skeletons/SkeletonResults";
import { CATEGORY_USER_EXAMS, CATEGORY_USERS } from "@/constants";
import { useAuth } from "@/context/auth";
import { useRBAC } from "@/context/rbac";
import { SCOPE_USER, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import UserResultsEmptyState from "./UserResultsEmptyState";

type TUserResults = {
    user_id: string;
}

const UserResults : React.FC<TUserResults> = ({ user_id }) => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [exam, setExam] = useState<IExam>();
    const [options, setOptions] = useState<IExam[]>([]);
    const { user } = useAuth()
    const { hasScopePermission } = useRBAC()

    const queryClient = useQueryClient();
    const t = useTranslations();
    const { page, query, page_size, setPagination } : IPaginationStore = usePaginationStore();

    const { data, isLoading, error } = useQuery({ 
        queryKey: [CATEGORY_USER_EXAMS, page, user_id], 
        queryFn: () => getExamsResultsByUserId(user_id), 
        retryOnMount: false, retry: false,
        enabled: mounted
    });

    const { data: userData, isLoading: isLoadingUser } = useQuery({
        queryKey: [CATEGORY_USERS], 
        queryFn: () => getUserById(user_id), 
        retryOnMount: false, retry: false,
        enabled: mounted && hasScopePermission([SCOPE_USER_IMPERSONATE]) ? true : false
    });

    useEffect(() => {
        if (error) toast.warn(t('toast.errors.loading.error_loading_user_exams'));
        if (data) {
            if (Array.isArray(data) && !isEmpty(data)) {
                setExam(data[0]);
                setOptions(data);
            }
        }
    }, [data, t, error]);

    useEffect(() => {
        if (mounted) {
            setPagination('show_finished', true)
            queryClient.invalidateQueries({ queryKey: ['user_exams'] });
            queryClient.invalidateQueries({ queryKey: ['user'] });
        }
    }, [mounted, page_size, query, queryClient, setPagination]);
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, [mounted]);

    if (isLoading) return <SkeletonResults />;
    if (!data || !options || isEmpty(options) || isEmpty(data)) return <UserResultsEmptyState />;
    if (error) return <>could not load data</>;
    
    const handleSelectExam = (id: string) => {
        const exam = options.find((exam: IExam)=> exam.id === id);
        if (!exam) return;
        setExam(exam)
    }

    return (
        <div className="w-full">
            <div className="flex flex-col gap-5 justify-between">
                <div className='w-full sm:w-80'>
                    <Select onValueChange={handleSelectExam}>
                        <SelectTrigger className="text-black dark:text-white">
                            <SelectValue placeholder={exam?.name} />
                        </SelectTrigger>
                        <SelectContent>
                            {options?.map((option : IExam) => (
                                <SelectItem key={option.id} value={option.id} className="text-black dark:text-white">
                                    {option.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <h2 className="w-full text-center text-2xl text-black dark:text-white my-6">
                    {hasScopePermission([SCOPE_USER]) ? user?.user_name : userData?.name}
                </h2>

                <section>
                    {exam && <ExamResult exam_id={exam.id} user_id={user_id}/>}
                </section>
            </div>
        </div>
    );
}

export default UserResults;