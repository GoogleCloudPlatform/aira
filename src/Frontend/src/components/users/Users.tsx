'use client';

import { getUsersWithExams, getExportedUsers, getUserById, getUsers, deleteUserById } from "@/services/user";
import { useEffect, useState } from "react";
import { 
    ColumnDef 
} from "@tanstack/react-table"; 
import { IUser } from "@/interfaces/auth";
import { SCOPE_ADMIN, SCOPE_USER_IMPERSONATE } from "@/constants/rbac";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { RBACWrapper, useRBAC } from "@/context/rbac";
import { ActionTable  } from "@/components";
import { SchemaCreateUserDefaultValues, SchemaCreateUserForm, SchemaEditUserForm, SchemaImportUser, SchemaImportUserDefaultValues } from "@/forms/user/schema";
import { TActionSheetOptions } from "@/interfaces/component";
import { isEmpty } from "lodash";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";
import { useTranslations } from "next-intl";
import { usePaginationStore } from "@/store/pagination";
import { TTableHeader } from "@/interfaces/table";
import { ENUM_EXAM_STATUS_FINISHED, ENUM_EXAM_STATUS_IN_PROGRESS, ENUM_EXAM_STATUS_NOT_STARTED } from "@/constants/enums";
import FormEditUser from "@/forms/user/FormEditUser";
import FormCreateUser from "@/forms/user/FormCreateUser";
import { CATEGORY_GROUPS, CATEGORY_USERS, MODE_CREATE, MODE_DELETE, MODE_EDIT, MODE_IMPORT, VALUE_NONE } from "@/constants";
import FormImportUser from "@/forms/user/FormImportUser";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import SkeletonUsers from "../skeletons/SkeletonUsers";
import Search from "../search/Search";
import { useUserStore } from "@/store/users";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { IGroupsResponse } from "@/interfaces/group";
import { getAllGroups } from "@/services/group";
import FormDeleteUser from "@/forms/user/FormDeleteUser";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { LucideBookCopy, LucideEdit, LucideLineChart, LucideTrash2, MoreHorizontal } from "lucide-react";
  
const Users : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);

    const t = useTranslations();
    const queryClient = useQueryClient();
    const { hasScopePermission } = useRBAC();
    const pathname = usePathname();
    const router = useRouter();
    const searchParams = useSearchParams();    
    const { setUser } = useUserStore();
    const { page, page_size, query, show_finished, setPagination } = usePaginationStore();

    const groups = searchParams.get("groups") || "";

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: [CATEGORY_USERS] });
        }
    }, [mounted, show_finished, groups, page_size, query, queryClient]);

    useEffect(() => {
        setMounted(true);

        return () => {
            setPagination('page_size', 10)
            setMounted(false);
        }
    }, [setPagination]);
    
    const { data, isLoading } = useQuery({
        queryKey: [CATEGORY_USERS, page], 
        queryFn: hasScopePermission([SCOPE_ADMIN]) ? getUsers : getUsersWithExams, 
        retryOnMount: false, retry: false,
        enabled: mounted
    });
    
    const { data: groupsOptions, isLoading: isLoadingGroups } = useQuery<IGroupsResponse | null>({ 
        queryKey: [CATEGORY_GROUPS], 
        queryFn: () => hasScopePermission([SCOPE_USER_IMPERSONATE]) ? getAllGroups() : null,
        retryOnMount: false, retry: false,
    });
    
    useEffect(() => {

        if (pathname.includes('/users/results')) {
            setPagination("show_finished", true);
        } else if (pathname.includes('/users/exams')) {
            setPagination("show_finished", false);
        }

    }, [setPagination, pathname]);

    if (isLoading || isLoadingGroups) return <SkeletonUsers />;
    if (!mounted || !data) return null;
    if (hasScopePermission([SCOPE_USER_IMPERSONATE]) && !groupsOptions) return null;
    

    const handleGroupChange = (value: any) => {
        if (value === VALUE_NONE) {
            router.push("/users/exams")    
            return;
        }

        router.push(`${pathname}?groups=${value}`);        
    }

    const create = async () => {
        setOptions({
            mode: MODE_CREATE,
            title: "form.user.create.create_user",
            subtitle: "form.user.create.create_subtitle_user",
            formData: {
                schema: SchemaCreateUserForm,
                defaultValues: SchemaCreateUserDefaultValues,
                category: CATEGORY_USERS,
            }
        });
        setOpenSheet(true);
    };

    const editById = async (id: string) => {
        setOptions({
            mode: MODE_EDIT,
            title: "form.user.edit.edit_user",
            subtitle: "form.user.edit.edit_subtitle_user",
            formData: {
                schema: SchemaEditUserForm,
                defaultValues: () => getUserById(id),
                category: CATEGORY_USERS,
            }
        });
        setOpenSheet(true);
    };

    const importUsers = () => {
        setOptions({
            mode: MODE_IMPORT,
            title: "form.user.import.import_user",
            subtitle: "form.user.import.import_subtitle_user",
            formData: {
                schema: SchemaImportUser,
                defaultValues: SchemaImportUserDefaultValues,
                category: CATEGORY_USERS,
            }
        });
        setOpenSheet(true);
    };
    
    const impersonate = (user : Partial<IUser>) => router.push(`/users/${user.id}/exams`);

    const results = (user : Partial<IUser>) => {
        setUser("user", user)
        router.push(`/users/${user.id}/results`);
    }
    
    const exportUsers = async () => {
        const data = await getExportedUsers();
        if (!data) return;
        window.open(data.url, "_blank");
    };

    const deleteById = (id: string) => {
        setOptions({
            mode: MODE_DELETE,
            title: "title",
            subtitle: "subtitle",
            formData: {
                confirm: async () => await deleteUserById(id),
                category: CATEGORY_USERS
            }
        });
    };
    
    const calculateDisabledExams = (item: any) => {
        if (!item || !item.exams || !item.exams.length) return true;

        let isDisabled = true;
        const hasExamToFinish = item.exams.find((exam : { status: string }) => exam.status !== ENUM_EXAM_STATUS_FINISHED);
        if (hasExamToFinish) isDisabled = false;

        return isDisabled;
    }

    const calculateDisabledResult = (item: any) => {
        if (!item || !item.exams || !item.exams.length) return true;

        let isDisabled = true;
        const canViewResults = item.exams.find((exam : { status: string }) => exam.status !== ENUM_EXAM_STATUS_NOT_STARTED && exam.status !== ENUM_EXAM_STATUS_IN_PROGRESS);
        if (canViewResults) isDisabled = false;

        return isDisabled;
    }
    
    const columns: ColumnDef<TTableHeader>[] = [
        {
            accessorKey: "name",
            header: t("table.headers.name"),
        },
        {
            accessorKey: "email_address",
            header: t("table.headers.email"),
        },
        {
            accessorKey: "actions",
            header: t("table.headers.actions"),
            cell: ({ row }) => {
                const user = row.original

                return (
                    <>
                        <div className="flex justify-center">
                            <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                                {pathname.includes('results') ?
                                    <Button
                                        variant={"secondary"}
                                        className="flex text-xs gap-1"
                                        onClick={() => results(user)}
                                        disabled={calculateDisabledResult(user)}
                                    >
                                        <LucideLineChart className="w-4 h-4" />
                                        {t('table.buttons.go_to_results')}
                                    </Button>
                                    :
                                    <Button
                                        variant={"secondary"}
                                        className="flex text-xs gap-1"
                                        onClick={() => impersonate(user)}
                                        disabled={calculateDisabledExams(user)}
                                    >
                                        <LucideBookCopy className="w-4 h-4" />
                                        {t('table.buttons.go_to_exams')}
                                    </Button>
                                }
                            </RBACWrapper>

                            <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" className="h-8 w-8 p-0">
                                            <span className="sr-only">{t('table.messages.open')}</span>
                                            <MoreHorizontal className="h-4 w-4" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem
                                            className="cursor-pointer flex justify-between text-xs"
                                            onClick={() => editById(user.id)}
                                        >
                                            {t('table.buttons.edit')}
                                            <LucideEdit className="w-4 h-4" />
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem
                                            className="cursor-pointer flex justify-between text-xs"
                                            onClick={() => deleteById(user.id)}
                                        >
                                            {t('table.buttons.delete')}
                                            <LucideTrash2 className="w-4 h-4" />
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </RBACWrapper>
                        </div>
                    </>
                );
            }
        },
    ];

    return (
        <>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 2xl:mt-10 sm:container">
                <div className="flex flex-col sm:flex-row gap-2 justify-between w-full">
                    <div className='w-full sm:w-80'>
                        <Search />
                    </div>    
                    <RBACWrapper requiredScopes={[SCOPE_USER_IMPERSONATE]}>
                        <div className="flex space-x-5 w-full sm:w-fit">
                            {/* <div className="flex items-center space-x-2 sm:ml-3">
                                <Switch 
                                    id="exam-type" 
                                    onCheckedChange={handleShowFinishedChange} 
                                    className="data-[state=checked]:bg-white data-[state=unchecked]:bg-gray-700"
                                />
                                <Label htmlFor="exam-type" className="cursor-pointer">
                                    {t('exam.show_all_exams')}
                                </Label>
                            </div> */}
                            <div className="w-full sm:w-fit">
                                <Select onValueChange={handleGroupChange} defaultValue={groups}>
                                    <SelectTrigger className="sm:w-[180px] w-full text-black dark:text-white">
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
                            </div>
                        </div>
                    </RBACWrapper>
                </div>

                <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
                    <div className="grid grid-flow-col space-x-2">
                        <Button onClick={importUsers}>
                            {t('table.buttons.import')}
                        </Button>
                        <Button onClick={exportUsers}>
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
                            {options.mode === MODE_CREATE && <FormCreateUser setOpen={setOpenSheet} {...options} />}
                            {options.mode === MODE_EDIT && <FormEditUser setOpen={setOpenSheet} {...options} />}
                            {options.mode === MODE_IMPORT && <FormImportUser setOpen={setOpenSheet} {...options} />}
                        </div>
                    </SheetContent>
                </Sheet>
            }

            {options.mode === MODE_DELETE && <FormDeleteUser setOpen={() => setOptions({} as TActionSheetOptions)} {...options} />}
        </>
    );
}

export default Users;