import { useRouter } from "next/router";
import useIcon from "@/hooks/useIcon/useIcon";
import { ICON_PLUS } from "@/constants/icons";
import { IAction } from "@/interfaces/actions";
import { ACTION_CANCEL, ACTION_CREATE, ACTION_DELETE, ACTION_EDIT, ACTION_GET_BY_ID, ACTION_GET_BY_ID_REDIRECT } from "@/constants/actions";
import Modal from "../modal/Modal";
import { useModalStore } from "@/store/modal";
import { IInput } from "@/interfaces/form";
import useForm from "@/hooks/useForm/useForm";
import { getModalInfo, getField, getFieldByKey, getFilledFormFields, getFormFields } from "@/utils/form";
import { IActionTable, IActionTableInfoData } from "@/interfaces/table";
import { isEmpty, isObject } from "lodash";
import Pagination from "../pagination/Pagination";
import { RBACWrapper } from "@/context/rbac";
import { useTranslation } from "react-i18next";
import { getFormattedDate } from "@/utils";
import NoData from "../no-data/NoData";
import { useEffect, useRef, useState } from "react";

const ActionTable : React.FC<IActionTable> = ({ data, fields, actions, pagination }) => {

    const [sticky, setSticky] = useState<number>(0);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const tableRef = useRef<HTMLTableElement>(null);
    const childRefs = useRef<any>([]);

    const { t } = useTranslation();
    const router = useRouter();
    const { asPath, query, locale } = router;

    const { getIcon } = useIcon();
    const { message, setModal } = useModalStore();
    const { inputs, setForm, createInput } = useForm();

    const { items } = data;
    const create = actions.find(a => a.name === ACTION_CREATE);

    useEffect(() => {
        const parentRect = wrapperRef.current?.getBoundingClientRect();
    
        const handleScroll = () => {
            childRefs.current.forEach((childRef : any) => {
                const childRect = childRef.getBoundingClientRect();
                const distanceFromParent = childRect.top - parentRect!.top;
                
                if (distanceFromParent < 0 && childRect.top > 150) {
                    const { id } = childRef.dataset;
                    setSticky(id);   
                }
            });
        }

        const el = wrapperRef.current;
        el?.addEventListener("scroll", handleScroll);

        return () => {
            el?.removeEventListener("scroll", handleScroll)
        }
    }, []);

    const cancel = () => {
        setForm("inputs", []);
        setModal("open", false);
    }

    const add = async () => {
        if (!create) return;

        const customData = getModalInfo(asPath) as IActionTableInfoData;
        if (isEmpty(customData)) return;

        const { icon, title, message } = customData.create;

        const formFields = await getFormFields(router, asPath, "create");

        if (!formFields || isEmpty(formFields)) return;

        setForm("inputs", formFields);
        setModal("icon", { icon: icon.icon, classes: icon.classes });
        setModal("title", title);
        setModal("actions", [
            { name: ACTION_CREATE, icon: "", classes: 'bg-blue-600 hover:bg-blue-700 text-white', action: () => create.action(), render: true }, 
            { name: ACTION_CANCEL, icon: "", classes: 'bg-white ring-gray-300 hover:bg-gray-50', action: () => cancel(), render: true }, 
        ] as Array<IAction>);
        setModal("open", true);
    } 

    const remove = (item : any) => {
        const action = actions.find(a => a.name === ACTION_DELETE);

        if (!action) return;

        const customData = getModalInfo(asPath) as IActionTableInfoData;
        if (isEmpty(customData)) return;
        const { icon, title, message } = customData.delete;
        
        setForm("inputs", []);
        setModal("icon", { icon: icon.icon, classes: icon.classes });
        setModal("title", title);
        setModal("message", `${t(message, { ns: "modal" })} ${getFieldByKey(router, item)}?`);
        setModal("actions", [
            { name: ACTION_DELETE, icon: "", classes: 'bg-red-600 hover:bg-red-700 text-white', action: () => action.action(item.id), render: true }, 
            { name: ACTION_CANCEL, icon: "", classes: 'bg-white ring-gray-300 hover:bg-gray-50', action: () => cancel(), render: true }, 
        ]);
        setModal("open", true);
    }

    const edit = async (item : any) => {
        const actionGetById = actions.find(a => a.name === ACTION_GET_BY_ID);
        const action = actions.find(a => a.name === ACTION_EDIT);
        
        if (!actionGetById) return;
        
        const data = await actionGetById.action(item.id);
        
        const customData = getModalInfo(asPath) as IActionTableInfoData;
        if (isEmpty(customData)) return;
        const { icon, title, message } = customData.edit;

        const formFields = await getFormFields(router, asPath, "edit");
        
        if (!formFields || isEmpty(formFields)) return;
        const filledData = getFilledFormFields(router, data, formFields);


        setForm("inputs", filledData);
        setModal("icon", { icon: icon.icon, classes: icon.classes });
        setModal("title", title);
        setModal("actions", [
            { name: ACTION_EDIT, icon: "", classes: 'bg-blue-600 hover:bg-blue-700 text-white', action: () => action && action.action(item.id), render: action?.render }, 
            { name: ACTION_CANCEL, icon: "", classes: 'bg-white ring-gray-300 hover:bg-gray-50', action: () => cancel(), render: true }, 
        ]);
        setModal("open", true);        
    }

    const getFunction = (action : IAction, item: any) => {
        if (action.name === ACTION_CREATE) return () => add();
        if (action.name === ACTION_DELETE) return () => remove(item);
        if (action.name === ACTION_EDIT) return () => edit(item);
        if (action.name === ACTION_GET_BY_ID) return () => action.render ? edit(item) : action.action(item.id);
        if (action.name === ACTION_GET_BY_ID_REDIRECT) return () => action.action(item.id);
        return () => console.warn("no_action");
    }

    const renderField = (item : any, field: any) => {
        if (field.includes("date") || field.includes("created") || field.includes("updated")) {
            return getFormattedDate(locale as string, new Date(item[field]));
        }

        return item[field];
    }
    
    const renderChildren = () => {
        if (!inputs) return null;

        if (!inputs.length) {
            return (
                <div className="w-full h-full flex flex-col gap-2">
                    {message}
                </div>
            )
        }

        return (
            <div className="w-full h-full flex flex-col gap-1 md:gap-2">
                <form id='form' onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-1">
                    {inputs.map((input : IInput, index : number) => input.render ? <div key={index}>{createInput(input, index)}</div> : null)}
                </form>
            </div>
        );
    } 


    const mobileTable = (
        <>
            <table ref={tableRef} className="min-w-full divide-y divide-gray-200 w-full text-sm text-left text-gray-500 md:table-fixed">    
                <tbody className="grid gap-2">
                    {items && items.map((item: any, index: number) => {

                        return (
                            <tr 
                                key={index} 
                                className={`bg-white border-b hover:bg-gray-50 divide-y divide-gray-50 text-xs ${index == sticky ? 'sticky top-0 z-20 bg-blue-50' : 'z-10'}`}
                                ref={(ref) => (childRefs.current[index] = ref)}
                                data-id={index}
                            >
                                {fields && fields.map((field : any, i : number) => {
                                    return (
                                        <td key={field} className={`grid grid-flow-col h-12 w-full ${i === 0 ? 'bg-gray-100 font-bold': ''}`}>
                                            <div className="text-start uppercase pl-2 h-12 items-center grid">
                                                {t(field, { ns: "fields" })}
                                            </div>
                                            <div className="grid gap-2 justify-center items-center h-12 text-center w-full">
                                                {isObject(item[field]) ? t(getField(router, item), { ns: "fields" }) : t(renderField(item, field), { ns: "fields" })}
                                            </div>
                                        </td>
                                    );
                                })}
                                {actions && actions.length ? 
                                    <td key={index} className="grid grid-flow-col text-center h-12 w-full">
                                        <div className="py-1 text-start uppercase items-center grid pl-2 h-full">
                                            {t("actions", { ns: "fields" })}
                                        </div>
                                        <div className="gap-2 justify-center h-full py-1 w-full items-center grid grid-flow-col">
                                            {actions.map((action : IAction, j : number) => {

                                                if (!action.render) return null;

                                                return (
                                                    <RBACWrapper key={j} requiredScopes={action.scopes}>
                                                        <button 
                                                            className="w-8 h-8 bg-gray-200 sm:shadow-lg rounded-md p-2 hover:bg-gray-300"
                                                            onClick={getFunction(action, item)}
                                                        >
                                                            <div className="w-4 h-4">
                                                                {getIcon({ icon: action.icon, classes: action.classes })}
                                                            </div>
                                                        </button>
                                                    </RBACWrapper>
                                                );
                                            })}
                                        </div>
                                    </td>
                                    :
                                    null
                                }
                            </tr>
                        )
                    })}
                </tbody>
            </table>
            {pagination ? <Pagination {...data} /> : null}
        </>
    )

    return (
        <>
            {actions.length ? <Modal>{renderChildren()}</Modal> : null}
            <div className="flex flex-col gap-2 w-full h-full justify-center overflow-hidden">
                <div className="flex justify-end sm:absolute sm:top-0 sm:right-0 sm:m-10">
                    {create ? 
                        <RBACWrapper requiredScopes={create.scopes}>
                            <button 
                                type="button" 
                                className="text-white bg-green-600 hover:bg-green-700 rounded-lg text-sm px-5 py-2 text-center inline-flex items-center gap-1 h-10"
                                onClick={add}
                            >
                                <div className="w-5 h-5">
                                    {getIcon({ icon: ICON_PLUS, classes: create.classes })}
                                </div>
                                <span>{t("create", { ns: "admin" })}</span>
                            </button>
                        </RBACWrapper>
                        :
                        null
                    }
                </div>
                {!data || !items || !fields || !fields.length ? 
                    <>
                        <NoData message="no_records" />
                    </>
                    : 
                    <>
                        <div ref={wrapperRef}  className="relative overflow-x-auto shadow-md rounded-lg block sm:hidden border">
                            {mobileTable}
                        </div>
                        <div className="relative overflow-x-auto shadow-md sm:rounded-lg hidden sm:block">
                    
                            <table className="w-full text-sm text-left text-gray-500 md:table-fixed">
                                <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                                    <tr>
                                        {fields && fields.map((field : any, index : number) => (
                                            <th key={index} scope="col" className="px-6 py-3 md:min-w-[180px]">
                                                {t(field, { ns: "fields" })}
                                            </th>
                                        ))}
                                        {actions && actions.length ? <th scope="col" className="px-6 py-3 text-center">{t("actions", { ns: "fields" })}</th> : null}
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((item : any, index: number) => (
                                        <tr 
                                            key={index} 
                                            className={`bg-white border-b hover:bg-gray-50`}
                                        >
                                            {fields && fields.map((field : any) => (
                                                <td key={field} className="px-6 py-4 md:break-words">
                                                    {isObject(item[field]) ? t(getField(router, item), { ns: "fields" }) : t(renderField(item, field), { ns: "fields" })}
                                                </td>
                                            ))}
                                            {actions && actions.length ? 
                                                <td key={index} className="px-6 py-4 text-center">
                                                    <div className="flex gap-2 justify-center">
                                                        {actions.map((action : IAction, j : number) => {

                                                            if (!action.render) return null;

                                                            return (
                                                                <RBACWrapper key={j} requiredScopes={action.scopes}>
                                                                    
                                                                    <button 
                                                                        className="w-fit flex justify-center items-center h-8 bg-gray-200 sm:shadow-lg rounded-md p-2 hover:bg-gray-300 gap-1"
                                                                        onClick={getFunction(action, item)}
                                                                    >
                                                                        <div className="w-4 h-4">
                                                                            <span>{getIcon({ icon: action.icon, classes: action.classes })}</span>
                                                                        </div>
                                                                        {action.text ? <span className="text-sm">{t(action.text, { ns: "exam" })}</span> : null}
                                                                    </button>
                                                                </RBACWrapper>
                                                            );
                                                        })}
                                                    </div>
                                                </td>
                                                :
                                                null
                                            }
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {pagination ? <Pagination {...data} /> : null}
                        </div>
                    </>
                }
                
            </div>
        </>
    );
}

export default ActionTable;