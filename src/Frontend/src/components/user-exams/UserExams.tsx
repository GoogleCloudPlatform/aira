'use client';

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { isEmpty } from "lodash";
import { RBACWrapper, useRBAC } from "@/context/rbac";
import { 
    ColumnDef 
} from "@tanstack/react-table"; 
import { getExamById } from "@/services/exam";
import { usePaginationStore } from "@/store/pagination";
import { getFormattedDate } from "@/utils";

import { TTableHeader } from "@/interfaces/table";
import { TActionSheetOptions } from "@/interfaces/component";
import { IExam } from "@/interfaces/exam";
import { IPaginationStore } from "@/interfaces/store";
import { SchemaCreateExam, SchemaCreateExamDefaultValues, SchemaEditExam } from "@/forms/exam/schema";

import Search from "../search/Search";
import SkeletonExams from "../skeletons/SkeletonExams";
import FormCreateExam from "@/forms/exam/FormCreateExam";
import FormEditExam from "@/forms/exam/FormEditExam";
import { ActionTable  } from "@/components";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";

import { SCOPE_ADMIN, SCOPE_USER } from "@/constants/rbac";
import { CATEGORY_EXAMS, MODE_CREATE, MODE_EDIT, MODE_VIEW } from "@/constants";
import { getExamsByUserId } from "@/services/user";
import { LucideFileText } from "lucide-react";

type TUserExams = {
    user_id: string;
}

const UserExams : React.FC<TUserExams> = ({ user_id }) => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);

    const queryClient = useQueryClient();
    const { locale } = useParams()
    const router = useRouter();
    const t = useTranslations();
    const { page, query, page_size } : IPaginationStore = usePaginationStore();
    const { hasScopePermission } = useRBAC();

    const isStudent = hasScopePermission([SCOPE_USER]);

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: ['user_exams'] });
        }
    }, [mounted, page_size, query, queryClient]);
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, [mounted]);

    const { data, isLoading } = useQuery({ 
        queryKey: ['user_exams', page], 
        queryFn: () => getExamsByUserId(user_id), 
        retryOnMount: false, retry: false,
        enabled: mounted
    });

    if (isLoading) return <SkeletonExams />;
    if (!data) return null;

    const create = async () => {
        setOptions({
            mode: MODE_CREATE,
            title: "create_exam",
            subtitle: "subtitle_create_exam",
            formData: {
                schema: SchemaCreateExam,
                defaultValues: SchemaCreateExamDefaultValues,
                category: CATEGORY_EXAMS,
            }
        });
        setOpenSheet(true);
    };

    const viewById = async (id: string) => {
        setOptions({
            mode: MODE_VIEW,
            title: "edit_exam",
            subtitle: "subtitle_view_exam",
            formData: {
                schema: SchemaEditExam,
                defaultValues: () => getExamById(id),
                category: CATEGORY_EXAMS,
            }
        });
        setOpenSheet(true);
    };

    const editById = async (id: string) => {
        setOptions({
            mode: MODE_EDIT,
            title: "edit_exam",
            subtitle: "subtitle_edit_exam",
            formData: {
                schema: SchemaEditExam,
                defaultValues: () => getExamById(id),
                category: CATEGORY_EXAMS,
            }
        });
        setOpenSheet(true);
    };

    const makeExam = (id : string) => {
        if (isStudent) {
            router.push(`/exams/${id}/questions`);
            return;
        }
        router.push(`/users/${user_id}/exams/${id}/questions`);
    }

    const calculateDisabledExams = (item: IExam) : boolean => {
        const now = new Date();
        if (item.start_date >= now) return false;
        return true;
    }

    const columns: ColumnDef<TTableHeader>[] = [
        {
            accessorKey: "name",
            header: t("table.headers.name"),
        },
        {
            accessorKey: "start_date",
            header: t("table.headers.start_date"),
            cell: ({ row }) => {
                const date : string = row.getValue('start_date');
                const formattedDate = getFormattedDate(locale as string, new Date(date))
                return formattedDate;
            }
        },
        {
            accessorKey: "end_date",
            header: t("table.headers.end_date"),
            cell: ({ row }) => {
                const date : string = row.getValue('end_date');
                const formattedDate = getFormattedDate(locale as string, new Date(date))
                return formattedDate;
            }
        },
        {
            accessorKey: "actions",
            header: t("table.headers.actions"),
            cell: ({ row }) => {
                const exam = row.original;
                
                return (
                    <Button
                        variant={"secondary"}
                        className="flex text-xs gap-1"
                        onClick={() => makeExam(exam.id)}
                    >
                        <LucideFileText className="w-4 h-4" />
                        {t('table.buttons.start_exam')}
                    </Button>
                )
            }
        },
    ];

    return (
        <>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 2xl:mt-10 sm:mx-8">
                <div className='w-full sm:w-80'>
                    <Search />
                </div>
                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                    <div className="grid grid-flow-col space-x-2">
                        <Button onClick={create}>
                            {t('table.buttons.create')}
                        </Button>
                    </div>
                </RBACWrapper>
            </div>

            <section className="sm:container pt-5 2xl:pt-10">
                
                <ActionTable 
                    columns={columns} 
                    data={data}
                    pagination
                />
            
            </section>
            
            <Sheet open={openSheet} onOpenChange={setOpenSheet}>
                <SheetContent className="overflow-auto w-full sm:min-w-[420px]">
                    {!isEmpty(options) ? 
                        <SheetHeader>
                            <SheetTitle>{t(options.title)}</SheetTitle>
                            <SheetDescription>{t(options.subtitle)}</SheetDescription>
                        </SheetHeader>
                        :
                        null
                    }
                    <div className="py-5">
                        {options.mode === MODE_CREATE && <FormCreateExam formData={options.formData} setOpen={setOpenSheet} />}
                        {options.mode === MODE_VIEW && <FormEditExam {...options} setOpen={setOpenSheet} preview />}
                        {options.mode === MODE_EDIT && <FormEditExam {...options} setOpen={setOpenSheet} />}
                    </div>
                </SheetContent>
            </Sheet>
           
        </>
    );
}

export default UserExams;