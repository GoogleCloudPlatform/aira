'use client';

import { useEffect, useState } from "react";
import { ColumnDef } from "@tanstack/react-table";
import { SCOPE_ADMIN } from "@/constants/rbac";
import { RBACWrapper } from "@/context/rbac";
import { ActionTable } from "@/components";
import { TActionSheetOptions } from "@/interfaces/component";
import { isEmpty } from "lodash";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "../ui/sheet";
import { useTranslations } from "next-intl";
import { usePaginationStore } from "@/store/pagination";
import { TTableHeader } from "@/interfaces/table";
import { getSeries, getSeriesById, deleteSeriesById } from "@/services/series";
import FormSeries from "@/components/series/FormSeries";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { SchemaSeries, SchemaSeriesDefaultValues } from "@/forms/series/schema";
import { MODE_CREATE, MODE_DELETE, MODE_EDIT } from "@/constants";
import Search from "../search/Search";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu";
import { LucideEdit, LucideTrash2, MoreHorizontal } from "lucide-react";
import FormDelete from "../locations/FormDelete";

const Series : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    const [openSheet, setOpenSheet] = useState<boolean>(false);
    const [options, setOptions] = useState<TActionSheetOptions>({} as TActionSheetOptions);

    const t = useTranslations();
    const queryClient = useQueryClient();
    const { page, page_size, query, setPagination } = usePaginationStore();

    const CATEGORY_SERIES = "series";

    useEffect(() => {
        if (mounted) {
            queryClient.invalidateQueries({ queryKey: [CATEGORY_SERIES] });
        }
    }, [mounted, page, page_size, query, queryClient]);

    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, []);

    const { data, isLoading } = useQuery({
        queryKey: [CATEGORY_SERIES, page],
        queryFn: () => getSeries(),
        retryOnMount: false,
        retry: false,
        enabled: mounted
    });

    if (isLoading) return <p>Loading...</p>;
    if (!mounted || !data) return null;

    const create = () => {
        setOptions({
            mode: MODE_CREATE,
            title: "form.series.create.create_series",
            subtitle: "form.series.create.create_subtitle_series",
            formData: {
                schema: SchemaSeries,
                defaultValues: SchemaSeriesDefaultValues,
                category: CATEGORY_SERIES,
            }
        });
        setOpenSheet(true);
    };

    const editById = async (id: string) => {
        setOptions({
            mode: MODE_EDIT,
            title: "form.series.edit.edit_series",
            subtitle: "form.series.edit.edit_subtitle_series",
            formData: {
                schema: SchemaSeries,
                defaultValues: () => getSeriesById(id),
                category: CATEGORY_SERIES,
                id: id
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
                confirm: async () => await deleteSeriesById(id),
                category: CATEGORY_SERIES
            }
        });
    };

    const columns: ColumnDef<TTableHeader>[] = [
        {
            accessorKey: "name",
            header: t("table.headers.name"),
        },
        {
            accessorKey: "code",
            header: t("table.headers.code"),
        },
        {
            accessorKey: "actions",
            header: t("table.headers.actions"),
            cell: ({ row }) => {
                const series = row.original;
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
                                        onClick={() => editById(series.id)}
                                    >
                                        {t('table.buttons.edit')}
                                        <LucideEdit className="w-4 h-4" />
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        className="cursor-pointer flex justify-between text-xs"
                                        onClick={() => deleteById(series.id)}
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
            <div className="sm:container pt-5 2xl:pt-10 mb-10">
                <h1 className="font-semibold text-2xl md:text-3xl text-primary dark:text-white mb-1">{t('form.series.list_title')}</h1>
                <h2 className="text-black/80 dark:text-white/80 text-base md:text-xl">{t('form.series.list_subtitle')}</h2>
            </div>
            <div className="flex sm:flex-row flex-col gap-5 justify-between p-1 sm:container">
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
                    category={CATEGORY_SERIES}
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
                            {(options.mode === MODE_CREATE || options.mode === MODE_EDIT) && (
                                <FormSeries mode={options.mode} formData={options.formData} setOpen={setOpenSheet} />
                            )}
                        </div>
                    </SheetContent>
                </Sheet>
            }
            {options.mode === MODE_DELETE && (
                <FormDelete 
                    mode={options.mode} 
                    title={options.title} 
                    formData={options.formData} 
                    setOpen={() => setOptions({} as TActionSheetOptions)} 
                    t_prefix="form.series.delete"
                />
            )}
        </>
    );
};

export default Series;
