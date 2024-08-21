'use client';

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { isEmpty } from "lodash";
import { usePaginationStore } from "@/store/pagination";
import { IPaginationStore } from "@/interfaces/store";
import { getExamsResultsByUserId, } from "@/services/user";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { IExam } from "@/interfaces/exam";
import { toast } from "react-toastify";
import ExamResult from "./ExamResult";
import { useUserStore } from "@/store/users";
import SkeletonResults from "../skeletons/SkeletonResults";

type TUserResults = {
    user_id: string;
}

const UserResults : React.FC<TUserResults> = ({ user_id }) => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [exam, setExam] = useState<IExam>();
    const [options, setOptions] = useState<IExam[]>([]);

    const queryClient = useQueryClient();
    const t = useTranslations();
    const { page, query, page_size, setPagination } : IPaginationStore = usePaginationStore();
    const { user } = useUserStore();

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

    const { data, isLoading, error } = useQuery({ 
        queryKey: ['user_exams', page, user_id], 
        queryFn: () => getExamsResultsByUserId(user_id), 
        retryOnMount: false, retry: false,
        enabled: mounted
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

    if (isLoading || !options || isEmpty(options)) return <SkeletonResults />;
    if (!data) return null;
    if (error) return <>could not load data</>;
    
    const handleSelectExam = (id: string) => {
        const exam = options.find((exam: IExam)=> exam.id === id);
        if (!exam) return;
        setExam(exam)
    }

    return (
        <>
            <div className="flex flex-col gap-5 justify-between p-1 2xl:mt-10 sm:mx-8">
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

                <h2 className="w-full text-center text-2xl text-black dark:text-white">
                    {user ? user.name : ''}
                </h2>

                <section>
                    {exam && <ExamResult exam_id={exam.id} user_id={user_id}/>}
                </section>
            </div>
        </>
    );
}

export default UserResults;