'use client'

import { ICON_MAGNIFYING_GLASS } from "@/constants/icons";
import useIcon from "@/hooks/useIcon";
import { IPaginationStore } from "@/interfaces/store";
import { usePaginationStore } from "@/store/pagination";
import { isEmpty } from "lodash";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { ChangeEvent, useEffect, useState } from "react";
import { toast } from "react-toastify";
import { Input } from "../ui/input";
import { Button } from "../ui/button";

const Search : React.FC = () => {
    const [text, setText] = useState("");

    const router = useRouter();
    const t = useTranslations();
    const { page, query, setPagination } : IPaginationStore = usePaginationStore();
    const { getIcon } = useIcon();

    useEffect(() => {
        setText("");
        return () => {
            setPagination("page", 1)
            setPagination("query", "")
        }
    }, [router, setPagination]);

    const handleChange = (event : ChangeEvent<HTMLInputElement>) => {
        const { value } = event.currentTarget;
        setText(value);
    };

    const search = (e : any) => {
        e.preventDefault();
        if (text.length < 3 && !isEmpty(text)) {
            toast.warn(t("toast.warnings.search.warning_fill_search"));
            return;
        }
        setPagination("query", text);
        setPagination("page", 1);
    }

    return (
        <>
            <div className="flex items-center justify-start gap-2">
                <form className="w-full flex gap-2 text-black dark:text-white" onSubmit={(e) => search(e)}>
                    <Input 
                        className="w-full"
                        value={text}
                        onChange={handleChange}
                        placeholder={t("search.search")}
                        type="text"
                        onKeyDown={(e) => e.key === 'Enter' && document.getElementById("search__button")?.click() }
                        required={text.length < 3 && !isEmpty(text) ? true : false}
                        minLength={3}
                    />
                    <Button 
                        id="search__button"
                        type="button"
                        onClick={(e) => search(e)}
                        className="space-x-1"
                    >
                        <div className="w-5 h-5">
                            {getIcon({ icon: ICON_MAGNIFYING_GLASS, classes: "" })}
                        </div>
                        <span className="hidden lg:flex">{t("search.search")}</span>
                    </Button>
                </form>
            </div>
        </>
    );
}

export default Search;