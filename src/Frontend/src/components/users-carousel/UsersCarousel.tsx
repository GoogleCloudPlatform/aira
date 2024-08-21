'use client'

import { IUserResponse, IUsersResponse } from "@/interfaces/user";
import { Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext } from "../ui/carousel";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter, DrawerClose } from "../ui/drawer";
import { getAllUsersWithExams } from "@/services/user";
import { Button } from "../ui/button";
import { CATEGORY_GROUPS, CATEGORY_USERS, VALUE_NONE } from "@/constants";
import { SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRBAC } from "@/context/rbac";
import { LucideCircleUserRound } from "lucide-react";
import { toast } from "react-toastify";
import { useTranslations } from "next-intl";
import { ENUM_EXAM_STATUS_NOT_STARTED } from "@/constants/enums";
import { IExam } from "@/interfaces/exam";
import { useRouter } from "next/navigation";
import SkeletonUsersCarousel from "../skeletons/SkeletonUsersCarousel";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { IGroupsResponse } from "@/interfaces/group";
import { getAllGroups } from "@/services/group";
import { useEffect } from "react";
import { useExamsStore } from "@/store/exams";
import { IExamsStore } from "@/interfaces/store";

type TUsersCarouselProps = {
    open: boolean;
    setOpen: (value: boolean) => void;
}

const UsersCarousel : React.FC<TUsersCarouselProps> = ({ open, setOpen }) => {
    const t = useTranslations();
    const { hasScopePermission } = useRBAC();
    const router = useRouter();
    const queryClient = useQueryClient();

    const { group, setExams } : IExamsStore = useExamsStore();
    
    const { data, isLoading, isError } = useQuery<IUsersResponse | null>({ 
        queryKey: [CATEGORY_USERS],
        queryFn: () => hasScopePermission([SCOPE_USER_IMPERSONATE]) ? getAllUsersWithExams(group) : null,
        retryOnMount: false, retry: false,
    });

    const { data: groupsOptions, isLoading: isLoadingGroups } = useQuery<IGroupsResponse | null>({ 
        queryKey: [CATEGORY_GROUPS], 
        queryFn: () => hasScopePermission([SCOPE_USER_IMPERSONATE]) ? getAllGroups() : null,
        retryOnMount: false, retry: false,
    });

    const handleGroupChange = (value: string) => {
        if (value === "none") {
            setExams('group', undefined)
        } else {
            setExams('group', value)
        }
    }

    useEffect(()=>{
        queryClient.invalidateQueries({ queryKey: [CATEGORY_USERS] })      
    }, [group, queryClient])

    const handleUserClick = (user: IUserResponse) => {
        if (!user || !user.id) {
            toast.warn(t("toast.warnings.exam.user_not_found"));
            return;
        }

        if (!user.exams || !user.exams.length) {
            toast.warn(t("toast.warnings.exam.warning_no_exams"));
            return;
        }

        if (user.exams.length > 1) {
            router.push(`/users/${user.id}/exams`);
            return;
        } 
        
        // assure that the redirect exam is not started
        const examToGo = user.exams.find((exam : IExam)  => exam.status === ENUM_EXAM_STATUS_NOT_STARTED);
        if (!examToGo) return;

        router.push(`/users/${user.id}/exams/${examToGo.id}/questions`);
    }

    return (
        <>
            <Drawer open={open} onClose={() => setOpen(false)}>
                <DrawerContent>
                    <div className="mx-auto w-full max-w-[90%]">
                        <DrawerHeader className="px-0">
                            <DrawerTitle>{t('exam.titles.students')}</DrawerTitle>
                            <DrawerDescription>{t('exam.messages.select_student')}</DrawerDescription>
    
                            <Select onValueChange={handleGroupChange} defaultValue={group}>
                                <SelectTrigger className="sm:max-w-[300px] w-full text-black dark:text-white">
                                    <SelectValue placeholder={t('search.groups')} />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectGroup>
                                        <SelectItem value={VALUE_NONE}>{t('search.select_a_group')}</SelectItem>    
                                        {groupsOptions && groupsOptions.items.map(item => 
                                            <SelectItem key={item.id} value={item.id}>{item.name}</SelectItem>    
                                        )}
                                    </SelectGroup>
                                </SelectContent>
                            </Select>
                        
                        </DrawerHeader>
                        <section className="content">
                            {isLoading && <SkeletonUsersCarousel />}
                            {isError && <>Could not load data</>}
                            {data && data.items.length > 0 && (
                                <Carousel className="carousel w-full">
                                    <CarouselPrevious className="ml-[30px] md:ml-4 lg:ml-0 z-10"/>
                                    <CarouselContent>
                                        {data.items.sort((a, b) => a.name.localeCompare(b.name)).map((user: IUserResponse) => {
                                            const shouldRenderUser = user.exams.find((exam: IExam) => exam.status === ENUM_EXAM_STATUS_NOT_STARTED);
                                            if (!shouldRenderUser) return null;

                                            return (
                                                <CarouselItem key={user.id} className="cursor-pointer md:basis-1/2 lg:basis-1/4" onClick={() => handleUserClick(user)}>
                                                    <Button variant={"outline"} className="flex aspect-square items-center justify-center h-[180px] w-full">
                                                        <div className="flex flex-col gap-2 items-center">
                                                            <LucideCircleUserRound className="w-10 h-10" />
                                                            <span className="w-fit">
                                                                {user.name}
                                                            </span>
                                                        </div>
                                                    </Button>
                                                </CarouselItem>
                                            )
                                        })}
                                    </CarouselContent>
                                    <CarouselNext className="mr-[30px] md:mr-4 lg:mr-0" />
                                </Carousel> )} 
                            {!isLoading && data?.items.length === 0 && ( <p className="dark:text-white">{t('exam.messages.no_users_found')}</p> )
                            }
                        </section>
                        <DrawerFooter className="px-0">
                            <DrawerClose asChild>
                                <Button variant={"secondary"} onClick={() => setOpen(false)}>{t('exam.buttons.close')}</Button>
                            </DrawerClose>
                        </DrawerFooter>
                    </div>
                </DrawerContent>
            </Drawer>
        </>
    );
}

export default UsersCarousel;