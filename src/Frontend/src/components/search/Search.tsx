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
import { ICON_MAGNIFYING_GLASS } from "@/constants/icons";
import useIcon from "@/hooks/useIcon/useIcon";
import { IPaginationStore } from "@/interfaces/store";
import { usePaginationStore } from "@/store/pagination";
import { isEmpty } from "lodash";
import { useRouter } from "next/router";
import { ChangeEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

const Search : React.FC = () => {
    const [text, setText] = useState("");

    const router = useRouter();
    const { t } = useTranslation();
    const { page, query, setPagination } : IPaginationStore = usePaginationStore();
    const { getIcon } = useIcon();

    useEffect(() => {
        setText("");
    }, [router]);

    const handleChange = (event : ChangeEvent<HTMLInputElement>) => {
        const { value } = event.currentTarget;
        setText(value);
    };

    const search = (e : any) => {
        e.preventDefault();
        if (text.length < 3 && !isEmpty(text)) {
            toast.warn(t("warning_fill_search", { ns: "toast" }));
            return;
        }
        setPagination("query", text);
        setPagination("page", 1);
    }

    return (
        <>
            <div className="flex items-center justify-center gap-2 mt-3 px-3 sm:mt-0 sm:px-0">
                <form className="w-full flex gap-2" onSubmit={(e) => search(e)}>
                    <input 
                        name="search"
                        value={text}
                        onChange={handleChange}
                        type="text"
                        placeholder={t("search", { ns: "common" })}
                        className="w-full h-10 indent-3 border text-gray-500 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
                        onKeyDown={(e) => e.key === 'Enter' && document.getElementById("search__button")?.click() }
                        required={text.length < 3 && !isEmpty(text) ? true : false}
                        minLength={3}
                    />
                    <button 
                        id="search__button"
                        type="button"
                        className={`bg-blue-600 hover:bg-blue-700 text-white inline-flex justify-center rounded-md px-3 py-2 text-sm font-semibold shadow-sm sm:w-auto h-10 items-center gap-1 w-fit`}
                        onClick={(e) => search(e)}
                    >
                        <div className="w-5 h-5">
                            {getIcon({ icon: ICON_MAGNIFYING_GLASS, classes: "" })}
                        </div>
                        <span className="hidden sm:flex">{t("search", { ns: "common" })}</span>
                    </button>
                </form>
            </div>
        </>
    );
}

export default Search;