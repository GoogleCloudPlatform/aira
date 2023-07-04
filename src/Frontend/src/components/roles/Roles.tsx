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
import { ENDPOINT_ROLES } from "@/constants/endpoint";
import { IModalStore, IRolesStore, IPaginationStore } from "@/interfaces/store";
import { api } from "@/pages/api/api";
import { useEffect, useState } from "react";
import useSWR, { SWRResponse, mutate } from 'swr';
import ActionTable from "../action-table/ActionTable";
import { ICON_EYE } from "@/constants/icons";
import { IAction } from "@/interfaces/actions";
import { ACTION_GET_BY_ID } from "@/constants/actions";
import useForm from "@/hooks/useForm/useForm";
import { useModalStore } from "@/store/modal";
import { usePaginationStore } from "@/store/pagination";
import { getURL } from "@/utils";
import { useRolesStore } from "@/store/roles";
import { getRoleById } from "@/services/roles";
import { SCOPE_ADMIN } from "@/constants/rbac";
import NoData from "../no-data/NoData";
import { RBACWrapper } from "@/context/rbac";
import { IRole, IRolesResponse } from "@/interfaces/role";
import { ShimmerActionTable } from "../shimmer";

const Roles : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);

    const { roles, setRoles } : IRolesStore = useRolesStore();
    const { setModal } : IModalStore = useModalStore();
    const { query, page, page_size, setPagination } : IPaginationStore = usePaginationStore();
    const { setForm } = useForm();

    const url = getURL(ENDPOINT_ROLES, { page, page_size, q: query  });
    const { data, error, isLoading } : SWRResponse = useSWR(url , api, { revalidateIfStale: false, revalidateOnFocus: false, shouldRetryOnError: false, revalidateOnMount: true });

    useEffect(() => {
        setMounted(true);
        return () => {
            setModal("open", false);
            setForm("inputs", []);
            setPagination("page", 1);
            setRoles("roles", null);
            setPagination("query", "");
            mutate(null);
            setMounted(false);
        }
    }, [setModal, setForm, setPagination, setRoles]);

    useEffect(() => {
        if (data) setRoles("roles", data.data);
    }, [mounted, data, setRoles]);

    useEffect(() => {
        const queryString = `page=${page}&page_size=${page_size}&q=${query}`;
    
        const shouldMutate = () => {    
            const hasQueryString = url.includes(queryString);
            return hasQueryString;
        };        

        if (mounted) {
            if (shouldMutate() && roles && data && roles.current_page !== page && roles.current_page !== data.current_page) {
                mutate(`${ENDPOINT_ROLES}?${queryString}`);
            }            
        }

        return () => {
            mutate(null); // Clear SWR cache keys
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mounted, query, page, page_size, url, roles]);

    if (!mounted || !roles) return null;
    if (isLoading) return <ShimmerActionTable />;
    if (error) return <NoData />;

    const { items } = roles as IRolesResponse;
    const object : IRole | [] = items && items.length ? items[0] : [];
    const fields : Array<string> = Object.keys(object).filter(k => !["id"].includes(k));;
    const actions : Array<IAction> = [
        { name: ACTION_GET_BY_ID, icon: ICON_EYE, classes: 'text-green-500', action: (id : string) => getRoleById(id), render: true, scopes: [SCOPE_ADMIN] }, 
    ];

    return (
        <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
            <ActionTable 
                data={roles} 
                fields={fields}
                actions={actions}
                pagination
            />
        </RBACWrapper>
    );
}

export default Roles;