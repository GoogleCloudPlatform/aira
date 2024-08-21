'use client'

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { isEmpty } from "lodash";
import { RBACWrapper } from "@/context/rbac";
import { 
    ColumnDef 
} from "@tanstack/react-table"; 
import { getExams, getExamById } from "@/services/exam";
import { usePaginationStore } from "@/store/pagination";
import { getFormattedDate } from "@/utils";

import { IAction } from "@/interfaces/action";
import { TTableHeader } from "@/interfaces/table";
import { TActionSheetOptions } from "@/interfaces/component";
import { IPaginationStore } from "@/interfaces/store";
import { SchemaCreateExam, SchemaCreateExamDefaultValues, SchemaEditExam } from "@/forms/exam/schema";

import Search from "../search/Search";
import SkeletonExams from "../skeletons/SkeletonExams";
import FormCreateExam from "@/forms/exam/FormCreateExam";
import FormEditExam from "@/forms/exam/FormEditExam";
import { ActionTable  } from "@/components";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";

import { SCOPE_ADMIN, SCOPE_EXAM_LIST, SCOPE_USER } from "@/constants/rbac";
import { ICON_EYE, ICON_PENCIL, ICON_PENCIL_SQUARE } from "@/constants/icons";
import { ACTION_EDIT, ACTION_GET_BY_ID, ACTION_GET_BY_ID_REDIRECT } from "@/constants/actions";
import { CATEGORY_EXAMS, MODE_CREATE, MODE_EDIT, MODE_VIEW } from "@/constants";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { LucideEdit, LucideEye, MoreHorizontal } from "lucide-react";

const Exams : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);

    const t = useTranslations();
    const queryClient = useQueryClient();
    const { locale } = useParams()
    const router = useRouter();
    const { page, query, page_size, setPagination } : IPaginationStore = usePaginationStore();


    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: [CATEGORY_EXAMS] });
        }
    }, [mounted, page_size, query, queryClient]);
    
    useEffect(() => {
        setMounted(true);
        return () => {
            setPagination('page_size', 10)
            setMounted(false);
        }
    }, [mounted, setPagination]);

    const { data, isLoading } = useQuery({ 
        queryKey: [CATEGORY_EXAMS, page], 
        queryFn: () => getExams(), 
        retryOnMount: false, retry: false,
        enabled: mounted
    });

    if (isLoading) return <SkeletonExams />;
    if (!data) return null;

    const create = async () => {
        setOptions({
            mode: MODE_CREATE,
            title: "form.exam.create.title",
            subtitle: "form.exam.create.subtitle",
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
            title: "form.exam.preview.title",
            subtitle: "form.exam.preview.subtitle",
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
            title: "form.exam.edit.title",
            subtitle: "form.exam.edit.subtitle",
            formData: {
                schema: SchemaEditExam,
                defaultValues: () => getExamById(id),
                category: CATEGORY_EXAMS,
            }
        });
        setOpenSheet(true);
    };

    // const deleteById = (id: string) => {
    //     setOptions({
    //         mode: MODE_DELETE,
    //         title: "title",
    //         subtitle: "subtitle",
    //         formData: {
    //             confirm: async () => await deleteExamById(id),
    //             category: CATEGORY_EXAMS
    //         }
    //     });
    // };

    const makeExam = (id : string) => router.push(`/exams/${id}`);

    const calculateDisabledEdit = (item: any) => {
        const today = new Date();
        const start_date = new Date(item.start_date);
        start_date.setMinutes(start_date.getMinutes() - 30); // to allow a quick edition until 30 minutes before exam start date

        if (today <= start_date) return false; // allow edition
        return true;
    }

    const actions : Array<IAction> = [
        { 
            name: ACTION_EDIT, icon: ICON_PENCIL, classes: 'bg-blue-500', action: (id : string) => editById(id), 
            scopes: [SCOPE_ADMIN],
            disabled: (item) => calculateDisabledEdit(item),
            render: true,
        }, 
        { name: ACTION_GET_BY_ID_REDIRECT, icon: ICON_PENCIL_SQUARE, classes: 'text-green-500', action: (id : string) => makeExam(id), disabled: () => false, scopes: [SCOPE_USER, SCOPE_EXAM_LIST], text: "start_exam", render: true, }, 
        { name: ACTION_GET_BY_ID, icon: ICON_EYE, classes: 'bg-green-500', action: (id : string) => viewById(id), disabled: () => false , scopes: [SCOPE_ADMIN], render: true, }, 
        // { name: ACTION_DELETE, icon: ICON_TRASH, classes: 'bg-red-500', action: (id : string) => deleteById(id), scopes: [SCOPE_ADMIN], disabled: () => false, render: true }
    ];

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
                const exam = row.original

                return (
                    <div className="flex justify-center">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                    <span className="sr-only">{t('table.messages.open')}</span>
                                    <MoreHorizontal className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                {/* <DropdownMenuLabel>Actions</DropdownMenuLabel> */}
                                <DropdownMenuItem
                                    className="cursor-pointer flex justify-between text-xs"
                                    onClick={() => editById(exam.id)}
                                    disabled={calculateDisabledEdit(exam)}
                                >
                                    {t('table.buttons.edit')}
                                    <LucideEdit className="w-4 h-4" />
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    className="cursor-pointer flex justify-between text-xs"
                                    onClick={() => viewById(exam.id)}
                                >
                                    {t('table.buttons.preview')}
                                    <LucideEye className="w-4 h-4" />
                                </DropdownMenuItem>
                                {/* <DropdownMenuSeparator /> */}
                                {/* <DropdownMenuItem
                                    className="cursor-pointer flex justify-between text-xs"
                                    onClick={() => deleteById(exam.id)}
                                >
                                    {t('start_exam')}
                                    <LucideTrash2 className="w-4 h-4" />
                                </DropdownMenuItem> */}
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                );
            }
        },
    ];

    return (
        <>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 2xl:mt-10 sm:container">
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

            {/* {options.mode === MODE_DELETE && <FormDeleteExam {...options} setOpen={setOpenSheet} />} */}
        </>
    );
}

export default Exams;