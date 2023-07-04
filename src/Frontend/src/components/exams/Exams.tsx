import { SCOPE_ADMIN, SCOPE_LEARNER, SCOPE_USER } from "@/constants/rbac";
import { RBACWrapper, useRBAC } from "@/context/rbac";
import { useRouter } from "next/router";
import { api } from "@/pages/api/api";
import { ENDPOINT_EXAMS } from "@/constants/endpoint";
import useSWR, { SWRResponse, mutate } from 'swr'
import { useEffect, useState } from "react";
import { IExamsStore, IFormStore, IModalStore, IPaginationStore, ISettingsStore } from "@/interfaces/store";
import { useExamsStore } from "@/store/exams";
import { usePaginationStore } from "@/store/pagination";
import { IExam, IExamsResponse } from "@/interfaces/exams";
import { getURL } from "@/utils";
import { IAction } from "@/interfaces/actions";
import { ACTION_CREATE, ACTION_GET_BY_ID, ACTION_GET_BY_ID_REDIRECT } from "@/constants/actions";
import { ICON_EYE, ICON_PENCIL_SQUARE, ICON_PLUS } from "@/constants/icons";
import ActionTable from "../action-table/ActionTable";
import useForm from "@/hooks/useForm/useForm";
import { useFormStore } from "@/store/form";
import { useModalStore } from "@/store/modal";
import { createExam, getExamById } from "@/services/exams";
import NoData from "../no-data/NoData";
import { useSettingsStore } from "@/store/settings";
import { ShimmerActionTable } from "../shimmer";
import { isEmpty } from "lodash";
import { toast } from "react-toastify";
import { i18n } from "next-i18next";

const fetcher = (url: string) => api.get(url).then((res) => res.data);

const Exams : React.FC = () => {
    const [mounted, setMounted] = useState<boolean>(false);
    
    const router = useRouter();
    const { setSettings } : ISettingsStore = useSettingsStore();
    const { exams, setExams } : IExamsStore = useExamsStore();
    const { setModal } : IModalStore = useModalStore();
    const { getForm } : IFormStore = useFormStore();
    const { query, page, page_size, setPagination } : IPaginationStore = usePaginationStore();
    const { setForm, checkFormSubmit } = useForm();
    const { hasScopePermission } = useRBAC();

    useEffect(() => {
        setMounted(true);
        return () => {
            setModal("open", false);
            setForm("inputs", []);
            setPagination("page", 1);
            setSettings("loading", false);
            setExams("exams", null);
            setPagination("query", "");
            mutate(null);
            setMounted(false);
        }
    }, [setModal, setForm, setPagination, setSettings, setExams]);

    const url = getURL(ENDPOINT_EXAMS, { page: page, page_size: page_size, q: query });
    const { data, error, isLoading } : SWRResponse = useSWR<IExamsResponse, Error>(
        mounted ? url : null, 
        fetcher,
        { revalidateIfStale: false, revalidateOnFocus: false, shouldRetryOnError: false, revalidateOnMount: true }
    );

    useEffect(() => {
        if (data) {
            if (isEmpty(data.items)) toast.warn(i18n?.t('warning_no_exams', { ns: "toast" }));
            setExams("exams", data);
        }
    }, [mounted, data, setExams]);
    

    useEffect(() => {
        const queryString = `page=${page}&page_size=${page_size}&q=${query}`;
    
        const shouldMutate = () => {    
            const hasQueryString = url.includes(queryString);
            return hasQueryString;
        };        

        if (mounted) {
            if (shouldMutate() && exams && data && exams.current_page !== page && exams.current_page !== data.current_page) {
                mutate(`${ENDPOINT_EXAMS}?${queryString}`);
            }            
        }

        return () => {
            mutate(null); // Clear SWR cache keys
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mounted, query, page, page_size, url, exams]);

    if (!mounted || !exams) return null;
    if (isLoading) return <ShimmerActionTable />;
    if (error) return <NoData />;
    
    const clean = () => {
        setModal("open", false);
        setForm("inputs", []);
        setExams("finished", false);
        setSettings("loading", false);
    }

    const create = () => {
        if (checkFormSubmit()) return;
        const { inputs } = getForm();
        setSettings("loading", true);
        createExam(inputs).then(response => {
            mutate(url);
            clean();
        }).finally(() => setSettings("loading", false));
    };

    const { items } = exams as IExamsResponse;
    const object : IExam | [] = items && items.length ? items[0] : [];
    const fields  = Object.keys(object).filter(k => !["id"].includes(k));;
    const actions : Array<IAction> = [
        { name: ACTION_GET_BY_ID, icon: ICON_EYE, classes: 'text-green-500', action: (id : string) => getExamById(id), render: true , scopes: [SCOPE_ADMIN] }, 
        { name: ACTION_GET_BY_ID_REDIRECT, icon: ICON_PENCIL_SQUARE, classes: 'text-green-500', action: (id : string) => router.push(`/exams/${id}`), render: hasScopePermission([SCOPE_LEARNER]) , scopes: [SCOPE_LEARNER], text: "start_exam" }, 
        { name: ACTION_CREATE, icon: ICON_PLUS, classes: 'text-white', action: () => create(), render: false, scopes: [SCOPE_ADMIN] }, 
    ];

    return (
        <>
            <RBACWrapper requiredScopes={[SCOPE_LEARNER, SCOPE_ADMIN, SCOPE_USER]}>
                <ActionTable
                    data={exams}
                    fields={fields}
                    actions={actions}
                    pagination
                />
            </RBACWrapper>
        </>
    );
}

export default Exams;