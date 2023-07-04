// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { ENDPOINT_ORGANIZATIONS } from "@/constants/endpoint";
import { ICON_CHEVRON_LEFT, ICON_CHEVRON_RIGHT } from "@/constants/icons";
import { MAX_VISIBLE_PAGES, PAGINATION_OFFSET } from "@/constants/pagination";
import useIcon from "@/hooks/useIcon/useIcon";
import { IPaginationStore } from "@/interfaces/store";
import { IActionTablePagination } from "@/interfaces/table";
import { usePaginationStore } from "@/store/pagination";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const Pagination : React.FC<IActionTablePagination> = ({ items, pages, total }) => {
    const { t } = useTranslation();
    const { getIcon } = useIcon();

    const [mounted, setMounted] = useState<boolean>(false);
    const { page, page_size, setPagination } : IPaginationStore = usePaginationStore();

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
        <>
            <div className="flex items-center justify-between bg-white px-4 py-3 sm:px-6">
                <div className="flex flex-1 justify-between sm:hidden">
                    <button 
                        onClick={() => handlePagination(page - 1)}
                        className={page === 1 ? 
                            "min-w-[100px] justify-center relative flex cursor-not-allowed bg-gray-50 items-center rounded-md border border-gray-300 px-4 py-2 text-xs font-medium text-gray-400" 
                            :
                            "min-w-[100px] justify-center relative flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                        }
                        disabled={page === 1}
                    >
                        {t("previous", { ns: "common" })}
                    </button>
                    <button 
                        onClick={() => handlePagination(page + 1)}
                        className={page === pages ?
                            "min-w-[100px] cursor-not-allowed justify-center relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-gray-50 px-4 py-2 text-xs font-medium text-gray-400"
                            :
                            "min-w-[100px] justify-center relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                        }
                        disabled={page === pages}
                    >
                        {t("next", { ns: "common" })}
                    </button>
                </div>
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                    <div>
                        <p className="text-sm text-gray-700">
                            {t("showing", { ns: "common" })}{' '} 
                            <span className="font-medium">
                                {showing}
                            </span> 
                            {' '}{t("to", { ns: "common" })}{' '} 
                            <span className="font-medium">
                                {entries}
                            </span> 
                            {' '}{t("of", { ns: "common" })}{' '}
                            <span className="font-medium">
                                {total}
                            </span> 
                            {' '}{t("results", { ns: "common" })}
                        </p>
                    </div>
                    <div>
                        <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                            <button
                                className={page === 1 ? 
                                    'cursor-not-allowed relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 bg-gray-50 focus:z-20 focus:outline-offset-0' 
                                    : 
                                    'relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                                }
                                onClick={() => handlePagination(page - 1)}
                                disabled={page === 1}
                            >
                                <span className="sr-only">{t("previous", { ns: "common" })}</span>
                                <div className="w-5 h-5">
                                    {getIcon({ icon: ICON_CHEVRON_LEFT, classes: "" })}
                                </div>
                            </button>
                            {Array.from(Array(pages).keys()).map(i => {
                                const index = i + 1;
                                const shouldTruncate = pages > MAX_VISIBLE_PAGES && Math.abs(page - index) > PAGINATION_OFFSET - 1;

                                if (shouldTruncate) {
                                    if (index === 1 || index === pages) {
                                        // Show the first and last pages
                                        return (
                                            <button
                                                key={index}
                                                className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0"
                                                onClick={() => handlePagination(index)}
                                            >
                                                {index}
                                            </button>
                                        );
                                    } else if (index === page - PAGINATION_OFFSET || index === page + PAGINATION_OFFSET) {
                                        // Show the current page and the pages with an offset of PAGINATION_OFFSET
                                        return (
                                            <button
                                                key={index}
                                                className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0"
                                            >
                                                ...
                                            </button>
                                        );
                                    }
                                    
                                    return null;
                                }

                                return (
                                    <button 
                                        key={index} 
                                        className={`${index === page ? 'relative z-10 inline-flex items-center bg-blue-600 px-4 py-2 text-sm font-semibold text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700' : 'relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'}`}
                                        onClick={() => handlePagination(index)}
                                    >
                                        {index}
                                    </button>
                                );
                            })}
                            <button 
                                className={page === pages ?
                                    'cursor-not-allowed relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 bg-gray-50 focus:z-20 focus:outline-offset-0' 
                                    : 
                                    "relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0"
                                }
                                onClick={() => handlePagination(page + 1)}
                                disabled={page === pages}
                            >
                                <span className="sr-only">{t("next", { ns: "common" })}</span>
                                <div className="w-5 h-5">
                                    {getIcon({ icon: ICON_CHEVRON_RIGHT, classes: "" })}
                                </div>
                            </button>
                        </nav>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Pagination;