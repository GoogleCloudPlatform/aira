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
import { ENDPOINT_USERS } from "@/constants/endpoint";
import { IFormStore, IModalStore, IUsersStore, IPaginationStore, ISettingsStore } from "@/interfaces/store";
import { api } from "@/pages/api/api";
import { useEffect, useState } from "react";
import useSWR, { SWRResponse, mutate } from 'swr';
import ActionTable from "../action-table/ActionTable";
import { ICON_PENCIL, ICON_PLUS, ICON_TRASH } from "@/constants/icons";
import { IAction } from "@/interfaces/actions";
import { ACTION_CREATE, ACTION_DELETE, ACTION_EDIT, ACTION_GET_BY_ID } from "@/constants/actions";
import useForm from "@/hooks/useForm/useForm";
import { useModalStore } from "@/store/modal";
import { useFormStore } from "@/store/form";
import { usePaginationStore } from "@/store/pagination";
import { getURL } from "@/utils";
import { useUsersStore } from "@/store/users";
import { createUser, deleteUserById, getUserById, updateUserById } from "@/services/users";
import { SCOPE_ADMIN } from "@/constants/rbac";
import { IUser, IUsersResponse } from "@/interfaces/user";
import NoData from "../no-data/NoData";
import { useSettingsStore } from "@/store/settings";
import { ShimmerActionTable } from "../shimmer";
import { isEmpty } from "lodash";
import { toast } from "react-toastify";
import { useTranslation } from "react-i18next";
import { RBACWrapper } from "@/context/rbac";

const fetcher = (url: string) => api.get(url).then((res) => res.data);

const Users : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);

    const { t } = useTranslation();
    const { setSettings } : ISettingsStore = useSettingsStore();
    const { users, setUsers } : IUsersStore = useUsersStore();
    const { setModal } : IModalStore = useModalStore();
    const { getForm } : IFormStore = useFormStore();
    const { query, page, page_size, setPagination, getPagination } : IPaginationStore = usePaginationStore();
    const { setForm, checkFormSubmit } = useForm();

    useEffect(() => {
        setMounted(true);
        return () => {
            setModal("open", false);
            setForm("inputs", []);
            setPagination("page", 1);
            setSettings("loading", false);
            setUsers("users", null);
            setPagination("query", "");
            mutate(null);
            setMounted(false);
        }
    }, [setModal, setForm, setPagination, setSettings, setUsers]);

    const url = getURL(ENDPOINT_USERS, { page, page_size, q: query });
    const { data, error, isLoading } : SWRResponse = useSWR(
        mounted ? url : null, 
        fetcher,
        { revalidateIfStale: false, revalidateOnFocus: false, shouldRetryOnError: false, revalidateOnMount: true }
    );

    useEffect(() => {
        if (data) {
            if (isEmpty(data.items)) toast.warn(t('warning_no_users', { ns: "toast" }));
            setUsers("users", data);
        }
    }, [mounted, data, setUsers, t]);

    useEffect(() => {
        const queryString = `page=${page}&page_size=${page_size}&q=${query}`;
    
        const shouldMutate = () => {    
            const hasQueryString = url.includes(queryString);
            return hasQueryString;
        };        

        if (mounted) {
            if (shouldMutate() && users && data && users.current_page !== page && users.current_page !== data.current_page) {
                mutate(`${ENDPOINT_USERS}?${queryString}`);
            }            
        }

        return () => {
            mutate(null); // Clear SWR cache keys
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mounted, query, page, page_size, url, users]);

    if (!mounted || !users) return null;
    if (isLoading) return <ShimmerActionTable />;
    if (error) return <NoData />;

    const { items } = users as IUsersResponse;
    
    const clean = () => {
        setModal("open", false);
        setForm("inputs", []);
        setSettings("loading", false);
    }

    const create = () => {
        if (checkFormSubmit()) return;
        const { inputs } = getForm();
        setSettings("loading", true);
        createUser(inputs).then(response => {
            mutate(url)
            clean();
        }).finally(() => setSettings("loading", false));
    };
   

    const deleteById = (id : string) => {
        setSettings("loading", true);
        deleteUserById(id).then(response => {
            
            const showing = (page - 1) * page_size + 1;
            const entries = items.length === page_size ? page * page_size : users.total;

            if (showing >= entries && showing > 1) setPagination("page", 1);
            else mutate(url)


            clean();
        }).finally(() => setSettings("loading", false));
    }

    const editById = (id : string) => {
        if (checkFormSubmit()) return;
        const { inputs } = getForm();
        setSettings("loading", true);
        updateUserById(id, inputs).then(response => {
            mutate(url);
            clean();
        }).finally(() => setSettings("loading", false));
    }

    
    const object : IUser | [] = items && items.length ? items[0] : [];
    const fields : Array<string> = Object.keys(object).filter(k => !["id", "groups", "role_id", "organizations"].includes(k));
    const actions : Array<IAction> = [
        { name: ACTION_GET_BY_ID, icon: "", classes: '', action: (id : string) => getUserById(id), render: false, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_CREATE, icon: ICON_PLUS, classes: 'text-white', action: () => create(), render: false, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_EDIT, icon: ICON_PENCIL, classes: 'text-blue-500', action: (id : string) => editById(id), render: true, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_DELETE, icon: ICON_TRASH, classes: 'text-red-500', action: (id : string) => deleteById(id), render: true, scopes: [SCOPE_ADMIN] }
    ];

    return (
        <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
            <ActionTable 
                data={users} 
                fields={fields}
                actions={actions}
                pagination
            />
        </RBACWrapper>
    );
}

export default Users;