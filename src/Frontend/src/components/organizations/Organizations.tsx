'use client';

import { useEffect, useState } from "react";
import { 
    ColumnDef 
} from "@tanstack/react-table"; 
import { SCOPE_ADMIN } from "@/constants/rbac";
import { RBACWrapper } from "@/context/rbac";
import { ActionTable  } from "@/components";
import { TActionSheetOptions } from "@/interfaces/component";
import { isEmpty } from "lodash";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";
import { useTranslations } from "next-intl";
import { usePaginationStore } from "@/store/pagination";
import { TTableHeader } from "@/interfaces/table";
import { getOrganizations, getOrganizationById, getExportedOrganizations, deleteOrganizationById } from "@/services/organization";
import FormCreateOrganization from "@/forms/organization/FormCreateOrganization";
import FormEditOrganization from "@/forms/organization/FormEditOrganization";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { SchemaCreateOrganization, SchemaCreateOrganizationDefaultValues, SchemaEditOrganization, SchemaImportOrganization, SchemaImportOrganizationDefaultValues } from "@/forms/organization/schema";
import FormImportOrganization from "@/forms/organization/FormImportOrganization";
import { CATEGORY_ORGANIZATIONS, MODE_CREATE, MODE_DELETE, MODE_EDIT, MODE_IMPORT } from "@/constants";
import { IPaginationStore } from "@/interfaces/store";
import SkeletonOrganization from "../skeletons/SkeletonOrganizations";
import Search from "../search/Search";
import FormDeleteOrganization from "@/forms/organization/FormDeleteOrganization";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { LucideEdit, LucideTrash, LucideTrash2, MoreHorizontal } from "lucide-react";
  
const Organizations : React.FC = () => {
    
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [openDialog, setOpenDialog] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);

    const t = useTranslations();
    const { page, page_size, query, setPagination } : IPaginationStore = usePaginationStore();
    const queryClient = useQueryClient();

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: [CATEGORY_ORGANIZATIONS] });
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
        queryKey: [CATEGORY_ORGANIZATIONS, page],
        queryFn: getOrganizations,
        retryOnMount: false, retry: false,
        enabled: mounted
    });

    
    if (isLoading) return <SkeletonOrganization />;
    if (!mounted || !data) return null;

    //const getUserById = (id: string) => null;
    const create = async () => {
        //const formInputs = await getFormCategory("USERS", "CREATE");
        //setSheet("options", newOptions);
        setOptions({
            mode: MODE_CREATE,
            title: "form.organization.create.create_organization",
            subtitle: "form.organization.create.create_subtitle_organization",
            formData: {
                schema: SchemaCreateOrganization,
                defaultValues: SchemaCreateOrganizationDefaultValues,
                category: CATEGORY_ORGANIZATIONS,
            }
        });
        setOpenSheet(true);
    };

    const editById = async (id: string) => {
        setOptions({
            mode: MODE_EDIT,
            title: "form.organization.edit.edit_organization",
            subtitle: "form.organization.edit.edit_subtitle_organization",
            formData: {
                schema: SchemaEditOrganization,
                defaultValues: () => getOrganizationById(id),
                category: CATEGORY_ORGANIZATIONS,
            }
        });
        setOpenSheet(true);
    };

    const deleteById = (id: string) => {
        setOptions({
            mode: MODE_DELETE,
            title: "title",
            subtitle: "subtitle",
            formData: {
                confirm: async () => await deleteOrganizationById(id),
                category: CATEGORY_ORGANIZATIONS
            }
        });
    };
    
    const importOrganizations = () => {
        setOptions({
            mode: MODE_IMPORT,
            title: "form.organization.import.import_organization",
            subtitle: "form.organization.import.import_subtitle_organization",
            formData: {
                schema: SchemaImportOrganization,
                defaultValues: SchemaImportOrganizationDefaultValues,
                category: CATEGORY_ORGANIZATIONS,
            }
        });
        setOpenSheet(true);
    };
    
    const exportOrganizations = async () => {
        const data = await getExportedOrganizations();
        window.open(data?.url, "_blank");
    };

    const columns: ColumnDef<TTableHeader>[] = [
        {
            accessorKey: "name",
            header: t("table.headers.name"),
        },
        {
            accessorKey: "city",
            header: t("table.headers.city"),
        },
        {
            accessorKey: "region",
            header: t("table.headers.region"),
        },
        {
            accessorKey: "county",
            header: t("table.headers.county"),
        },
        {
            accessorKey: "actions",
            header: t("table.headers.actions"),
            cell: ({ row }) => {
                const organization = row.original

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
                                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs"
                                        onClick={() => editById(organization.id)}
                                    >
                                        {t('table.buttons.edit')}
                                        <LucideEdit className="w-4 h-4" />
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs"
                                        onClick={() => deleteById(organization.id)}
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

    return (
        <>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 2xl:mt-10 sm:container">
                <div className='w-full sm:w-80'>
                    <Search />
                </div>
                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                    <div className="grid grid-flow-col space-x-2">
                        <Button onClick={importOrganizations}>
                            {t('table.buttons.import')}
                        </Button>
                        <Button onClick={exportOrganizations}>
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
                            {options.mode === MODE_CREATE && <FormCreateOrganization setOpen={setOpenSheet} {...options} />}
                            {options.mode === MODE_EDIT && <FormEditOrganization setOpen={setOpenSheet} {...options} />}
                            {options.mode === MODE_IMPORT && <FormImportOrganization setOpen={setOpenSheet} {...options} />}
                        </div>
                    </SheetContent>
                </Sheet>
            }

            {options.mode === MODE_DELETE && <FormDeleteOrganization setOpen={() => setOptions({} as TActionSheetOptions)} {...options} />}
        </>
    );
}

export default Organizations;