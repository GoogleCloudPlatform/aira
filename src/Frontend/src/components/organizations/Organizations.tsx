import { ENDPOINT_ORGANIZATIONS } from "@/constants/endpoint";
import { IFormStore, IModalStore, IOrganizationsStore, IPaginationStore, ISettingsStore } from "@/interfaces/store";
import { api } from "@/pages/api/api";
import { useOrganizationsStore } from "@/store/organizations";
import { useEffect, useState } from "react";
import useSWR, { SWRResponse, mutate } from 'swr';
import ActionTable from "../action-table/ActionTable";
import { ICON_PENCIL, ICON_PLUS, ICON_TRASH } from "@/constants/icons";
import { IAction } from "@/interfaces/actions";
import { ACTION_CREATE, ACTION_DELETE, ACTION_EDIT, ACTION_GET_BY_ID } from "@/constants/actions";
import { createOrganization, deleteOrganizationById, getOrganizationById, updateOrganizationById } from "@/services/organization";
import useForm from "@/hooks/useForm/useForm";
import { useModalStore } from "@/store/modal";
import { useFormStore } from "@/store/form";
import { usePaginationStore } from "@/store/pagination";
import { getURL } from "@/utils";
import { SCOPE_ADMIN } from "@/constants/rbac";
import NoData from "../no-data/NoData";
import { RBACWrapper } from "@/context/rbac";
import { IOrganization, IOrganizationsResponse } from "@/interfaces/organization";
import { useSettingsStore } from "@/store/settings";
import { ShimmerActionTable } from "../shimmer";
import { isEmpty } from "lodash";
import { toast } from "react-toastify";
import { useTranslation } from "react-i18next";


const fetcher = (url: string) => api.get(url).then((res) => res.data);

const Organizations : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);

    const { t } = useTranslation();
    const { setSettings } : ISettingsStore = useSettingsStore();
    const { organizations, setOrganizations } : IOrganizationsStore = useOrganizationsStore();
    const { setModal } : IModalStore = useModalStore();
    const { getForm } : IFormStore = useFormStore();
    const { query, page, page_size, setPagination } : IPaginationStore = usePaginationStore();
    const { setForm, checkFormSubmit } = useForm();

    useEffect(() => {
        setMounted(true);
        return () => {
            setModal("open", false);
            setForm("inputs", []);
            setPagination("page", 1);
            setSettings("loading", false);
            setOrganizations("organizations", null);
            setPagination("query", "");
            mutate(null);
            setMounted(false);
        }
    }, [setModal, setForm, setPagination, setSettings, setOrganizations]);

    
    const url = getURL(ENDPOINT_ORGANIZATIONS, { page: page, page_size: page_size, q: query });
    const { data, error, isLoading } : SWRResponse = useSWR(
        mounted ? url : null,
        fetcher,
        { revalidateIfStale: false, revalidateOnFocus: false, shouldRetryOnError: false, revalidateOnMount: true }
    );

    useEffect(() => {
        if (data) {
            if (isEmpty(data.items)) toast.warn(t('warning_no_organizations', { ns: "toast" }));
            setOrganizations("organizations", data);
        }
    }, [mounted, data, setOrganizations, t]);

    useEffect(() => {
        const queryString = `page=${page}&page_size=${page_size}&q=${query}`;
    
        const shouldMutate = () => {    
            const hasQueryString = url.includes(queryString);
            return hasQueryString;
        };        

        if (mounted) {
            if (shouldMutate() && organizations && data && organizations.current_page !== page && organizations.current_page !== data.current_page) {
                mutate(`${ENDPOINT_ORGANIZATIONS}?${queryString}`);
            }            
        }

        return () => {
            mutate(null); // Clear SWR cache keys
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mounted, query, page, page_size, url, organizations]);

    if (!mounted || !organizations) return null;
    if (isLoading) return <ShimmerActionTable />;
    if (error) return <NoData />;

    const { items } = organizations as IOrganizationsResponse;

    const clean = () => {
        setModal("open", false);
        setForm("inputs", []);
        setSettings("loading", false);
    }

    const create = () => {
        if (checkFormSubmit()) return;
        const { inputs } = getForm();
        setSettings("loading", true);
        createOrganization(inputs).then(response => {
            mutate(url)
            clean();
        }).finally(() => setSettings("loading", false));
    };
   

    const deleteById = (id : string) => {
        setSettings("loading", true);
        deleteOrganizationById(id).then(response => {  
            const showing = (page - 1) * page_size + 1;
            const entries = items.length === page_size ? page * page_size : data.total;

            if (showing >= entries && showing > 1) setPagination("page", 1);
            else mutate(url)

            clean();
        }).finally(() => setSettings("loading", false));
    }

    const editById = (id : string) => {
        if (checkFormSubmit()) return;
        const { inputs } = getForm();
        setSettings("loading", true);
        updateOrganizationById(id, inputs).then(response => {
            mutate(url);
            clean();
        }).finally(() => setSettings("loading", false));
    }

    
    const object : IOrganization | [] = items && items.length ? items[0] : [];
    const fields : Array<string> = Object.keys(object).filter(k => !["id", "customer_id"].includes(k));
    const actions : Array<IAction> = [
        { name: ACTION_GET_BY_ID, icon: "", classes: '', action: (id : string) => getOrganizationById(id), render: false, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_CREATE, icon: ICON_PLUS, classes: 'text-white', action: () => create(), render: false, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_EDIT, icon: ICON_PENCIL, classes: 'text-blue-500', action: (id : string) => editById(id), render: true, scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_DELETE, icon: ICON_TRASH, classes: 'text-red-500', action: (id : string) => deleteById(id), render: true, scopes: [SCOPE_ADMIN] }
    ];

    return (
        <RBACWrapper requiredScopes={[SCOPE_ADMIN]}>
            <ActionTable 
                data={organizations} 
                fields={fields}
                actions={actions}
                pagination
            />
        </RBACWrapper>
    );
}

export default Organizations;