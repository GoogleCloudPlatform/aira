import { MAX_VISIBLE_PAGES, PAGINATION_OFFSET } from "@/constants/paginations";
import { IPaginationStore } from "@/interfaces/store";
import { IActionTablePagination } from "@/interfaces/table";
import { usePaginationStore } from "@/store/pagination";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";
import { Pagination, PaginationButton, PaginationButtonNext, PaginationButtonPrevious, PaginationContent, PaginationEllipsis, PaginationItem } from "../ui/pagination";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

const PaginationTable : React.FC<IActionTablePagination> = ({ items, pages, total }) => {
    const t = useTranslations();

    const [mounted, setMounted] = useState<boolean>(false);
    const { page, page_size, setPagination } : IPaginationStore = usePaginationStore();
    
    const options = ["5", "10", "15", "20", "25", "50"];

    const showing = (page - 1) * page_size + 1;
    const entries = items.length === page_size ? page * page_size : total;

    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
        }
    }, []);

    const handlePagination = useCallback((index : number) => {
        if (index < 1) return;
        setPagination("page", index);
    }, [setPagination]);

    if (!mounted) return null;
    
    return (
        <div className="flex">
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div className="flex gap-2 items-center">
                    <p className="text-sm">
                        {t("table.pagination.showing")}{' '} 
                        <span className="font-medium">
                            {showing}
                        </span> 
                        {' '}{t("table.pagination.to")}{' '} 
                        <span className="font-medium">
                            {entries}
                        </span> 
                        {' '}{t("table.pagination.of")}{' '}
                        <span className="font-medium">
                            {total}
                        </span> 
                        {' '}{t("table.pagination.results")}
                    </p>
                    <div>
                        <Select 
                            onValueChange={(value) => {
                                setPagination("page_size", value)
                            }} 
                            defaultValue={page_size.toString()}
                        >
                            <SelectTrigger className="w-[65px]">
                                <SelectValue placeholder={"5"} />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    {options.map(o => 
                                        <SelectItem key={o} value={o}>
                                            {o}
                                        </SelectItem>
                                    )}
                                </SelectGroup>
                            </SelectContent>
                        </Select>                      
                    </div>
                </div>
            </div>
            <div className="w-full sm:w-fit">
                <Pagination>
                    <PaginationContent>
                        <PaginationItem>
                            <PaginationButtonPrevious 
                                name={t('table.pagination.previous')} 
                                onClick={() => handlePagination(page - 1)} 
                                disabled={page === 1} 
                            />
                        </PaginationItem>
                        {Array.from(Array(pages).keys()).map(i => {
                            const index = i + 1;
                            const shouldTruncate = pages > MAX_VISIBLE_PAGES && Math.abs(page - index) > PAGINATION_OFFSET - 1;

                            if (shouldTruncate) {
                                if (index === 1 || index === pages) {
                                    // Show the first and last pages
                                    return (
                                        <PaginationItem key={index}>
                                            <PaginationButton>
                                                {index}
                                            </PaginationButton>
                                        </PaginationItem>
                                    );
                                } else if (index === page - PAGINATION_OFFSET || index === page + PAGINATION_OFFSET) {
                                    // Show the current page and the pages with an offset of PAGINATION_OFFSET
                                    return (
                                        <PaginationItem key={index}>
                                            <PaginationEllipsis />
                                        </PaginationItem>
                                    );
                                }
                                    
                                return null;
                            }

                            return (
                                <PaginationItem key={index}>
                                    <PaginationButton isActive={index === page} onClick={() => handlePagination(index)}>
                                        {index}
                                    </PaginationButton>
                                </PaginationItem>
                            );
                        })}
                        <PaginationItem>
                            <PaginationButtonNext 
                                name={t('table.pagination.next')} 
                                onClick={() => handlePagination(page + 1)}
                                disabled={page >= pages}
                            />
                        </PaginationItem>
                    </PaginationContent>
                </Pagination>
            </div>
        </div>
    )
}

export default PaginationTable;