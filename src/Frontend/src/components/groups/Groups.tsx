'use client';

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
    ColumnDef 
} from "@tanstack/react-table"; 
import { useTranslations } from "next-intl";
import { isEmpty } from "lodash";
import { RBACWrapper } from "@/context/rbac";
import { getGroups, getGroupById, getExportedGroups, deleteGroupById } from "@/services/group";
import { usePaginationStore } from "@/store/pagination";
import { getFormattedDate } from "@/utils";

import { TActionSheetOptions } from "@/interfaces/component";
import { TTableHeader } from "@/interfaces/table";
import { IPaginationStore } from "@/interfaces/store";
import { SchemaCreateGroup, SchemaEditGroup, SchemaImportGroup, SchemaCreateGroupDefaultValues, SchemaImportGroupDefaultValues } from "@/forms/group/schema";

import Search from "../search/Search";
import FormCreateGroup from "@/forms/group/FormCreateGroup";
import FormEditGroup from "@/forms/group/FormEditGroup";
import FormImportGroup from "@/forms/group/FormImportGroup";
import SkeletonGroups from "../skeletons/SkeletonGroups";
import { Button } from "../ui/button";
import { ActionTable  } from "@/components";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";

import { SCOPE_ADMIN, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { CATEGORY_GROUPS, MODE_CREATE, MODE_DELETE, MODE_EDIT, MODE_IMPORT } from "@/constants";
import FormDeleteGroup from "@/forms/group/FormDeleteGroup";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { LucideEdit, LucideLineChart, LucideTrash2, MoreHorizontal, NotepadTextIcon } from "lucide-react";
  
const Groups : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);
    
    const t = useTranslations();
    const queryClient = useQueryClient();
    const { locale } = useParams()
    const router = useRouter()
    const { page, query, page_size, setPagination } : IPaginationStore = usePaginationStore();

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: [CATEGORY_GROUPS] });
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
        queryKey: [CATEGORY_GROUPS, page],
        queryFn: ()=> getGroups(),
        retryOnMount: false, retry: false,
        enabled: mounted
    });

    if (isLoading) return <SkeletonGroups />;
    if (!mounted || !data) return null;

    const create = async () => {
        setOptions({
            mode: MODE_CREATE,
            title: "form.group.create.create_group",
            subtitle: "form.group.create.create_subtitle_group",
            formData: {
                schema: SchemaCreateGroup,
                defaultValues: SchemaCreateGroupDefaultValues,
                category: CATEGORY_GROUPS,
            }
        });
        setOpenSheet(true);
    };
    
    const editById = async (id: string) => {
        setOptions({
            mode: MODE_EDIT,
            title: "form.group.edit.edit_group",
            subtitle: "form.group.edit.edit_subtitle_group",
            formData: {
                schema: SchemaEditGroup,
                defaultValues: () => getGroupById(id),
                category: CATEGORY_GROUPS,
            }
        });
        setOpenSheet(true);
    };
    
    const importGroups = () => {
        setOptions({
            mode: MODE_IMPORT,
            title: "form.group.import.import_group",
            subtitle: "form.group.import.import_subtitle_group",
            formData: {
                schema: SchemaImportGroup,
                defaultValues: SchemaImportGroupDefaultValues,
                category: CATEGORY_GROUPS,
            }
        });
        setOpenSheet(true);
    };
    
    const exportGroups = async () => {
        const data = await getExportedGroups();
        window.open(data?.url, "_blank");
    };
    
    const deleteById = (id : string) => {
        setOptions({
            mode: MODE_DELETE,
            title: "title",
            subtitle: "subtitle",
            formData: {
                confirm: async () => await deleteGroupById(id),
                category: CATEGORY_GROUPS
            }
        });
    }
    
    const columns: ColumnDef<TTableHeader>[] = [
        {
            accessorKey: "name",
            header: t("table.headers.name"),
        },
        {
            accessorKey: "grade",
            header: t("table.headers.grade"),
        },
        {
            accessorKey: "shift",
            header: t("table.headers.shift"),
            cell: ({ row }) => {
                const shift : string = row.getValue('shift');
                return t(`table.shifts.${shift}`);
            }
        },
        {
            accessorKey: "organization.name",
            header: t("table.headers.organization"),
        },
        {
            accessorKey: "created_at",
            header: t("table.headers.created_at"),
            cell: ({ row }) => {
                const date : string = row.getValue('created_at');
                const formattedDate = getFormattedDate(locale as string, new Date(date))
                return formattedDate;
            }
        },
        {
            accessorKey: "updated_at",
            header: t("table.headers.updated_at"),
            cell: ({ row }) => {
                const date : string = row.getValue('updated_at');
                const formattedDate = getFormattedDate(locale as string, new Date(date))
                return formattedDate;
            }
        },
        {
            accessorKey: "actions",
            header: t("table.headers.actions"),
            cell: ({ row }) => {
                const group = row.original

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
                                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs"
                                        onClick={() => editById(group.id)}
                                    >
                                        {t('table.buttons.edit')}
                                        <LucideEdit className="w-4 h-4" />
                                    </DropdownMenuItem>
                                </RBACWrapper>
                                
                                <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs px-2 gap-2"
                                        onClick={() => router.push(`/users/exams?groups=${group.id}`)}
                                    >
                                        {t('table.buttons.go_to_exams')}
                                        <NotepadTextIcon className="w-4 h-4" />
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs px-2 gap-2"
                                        onClick={() => router.push(`/users/results?groups=${group.id}`)}
                                    >
                                        {t('table.buttons.go_to_results')}
                                        <LucideLineChart className="w-4 h-4" />
                                    </DropdownMenuItem>
                                </RBACWrapper>

                                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs"
                                        onClick={() => deleteById(group.id)}
                                    >
                                        {t('table.buttons.delete')}
                                        <LucideTrash2 className="w-4 h-4" />
                                    </DropdownMenuItem>
                                </RBACWrapper>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                );
            }
        },
    ];

    const renderForm = () => {
        if (!options || isEmpty(options)) return null;

        if (options.mode === MODE_CREATE) {
            return <FormCreateGroup setOpen={setOpenSheet} {...options} />
        }

        if (options.mode === MODE_EDIT) {
            return <FormEditGroup setOpen={setOpenSheet} {...options} />;
        }

        if (options.mode === MODE_IMPORT) {
            return <FormImportGroup setOpen={setOpenSheet} {...options} />
        }

        return null;
    }

    return (
        <>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 2xl:mt-10 sm:container">
                <div className='w-full sm:w-80'>
                    <Search />
                </div>
                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                    <div className="grid grid-flow-col space-x-2">
                        <Button onClick={importGroups}>
                            {t('table.buttons.import')}
                        </Button>
                        <Button onClick={exportGroups}>
                            {t('table.buttons.export')}
                        </Button>
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

            {openSheet && 
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
                            {renderForm()}
                        </div>
                    </SheetContent>
                </Sheet>
            }
            {options.mode === MODE_DELETE && <FormDeleteGroup setOpen={() => setOptions({} as TActionSheetOptions)} {...options} />}
        </>
    );
}

export default Groups;