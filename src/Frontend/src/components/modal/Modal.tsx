import { ACTION_CANCEL } from "@/constants/actions";
import { ICON_X_MARK } from "@/constants/icons";
import useClickOutside from "@/hooks/useClickOutside/useClickOutside";
import useIcon from "@/hooks/useIcon/useIcon";
import { IAction } from "@/interfaces/actions";
import { IModalStore } from "@/interfaces/store";
import { useModalStore } from "@/store/modal";
import { PropsWithChildren, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

const Modal : React.FC<PropsWithChildren> = ({ children }) => {
    const modalRef = useRef<HTMLDivElement>(null);

    const { t } = useTranslation();
    const { open, icon, title, actions, setModal } : IModalStore = useModalStore();
    const { getIcon } = useIcon();

    useEffect(() => {
        let ignore = false;

        if (ignore) setModal("open", false);

        return () => {    
            ignore = true;
        }
    }, [open, actions, setModal]);

    useClickOutside(modalRef, () => setModal("open", false));

    const close = () => {
        const cancel = actions.find(a => a.name === ACTION_CANCEL);
        if (cancel && cancel.action) cancel.action();
        setModal("open", false);
    }

    if (!open) return null;

    return (
        <>
            <div className="relative z-40" aria-labelledby="modal-title" role="dialog" aria-modal="true" >
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity">
                    <div className="fixed inset-0 z-40 overflow-y-auto">
                        <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
                            <div className="relative transform rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 w-full sm:max-w-lg">
                                <div className="absolute p-2 top-0 right-0">
                                    <button onClick={close} className="w-5 h-5">
                                        {getIcon({ icon: ICON_X_MARK, classes: "text-gray-300" })}
                                    </button>
                                </div>
                                <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4 rounded-t-lg">
                                    <div className="sm:flex sm:items-start">
                                        {icon.icon !== "" ? 
                                            <div className={`mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${icon.classes} sm:mx-0 sm:h-10 sm:w-10`}>
                                                <div className="h-6 w-6">
                                                    {getIcon({ icon: icon.icon, classes: icon.classes })}
                                                </div>
                                            </div>
                                            :
                                            null
                                        }

                                        <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                                            {title !== "" ? 
                                                <h3 className="text-base font-semibold leading-6 text-gray-900" id="modal-title">
                                                    {t(title, { ns: "modal" })}
                                                </h3>
                                                :
                                                null
                                            }
                                            <div className="mt-2">
                                                <div className="text-sm text-gray-500 w-full">
                                                    {children}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {actions && actions.length ? 
                                    <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 gap-2 rounded-b-lg">
                                        {actions.map((action : IAction, index: number) => {
                                            if (!action.render) return null;

                                            return (
                                                <button 
                                                    key={index} 
                                                    type="submit"
                                                    form='form'
                                                    className={`${action.classes} inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold shadow-sm sm:ml-3 sm:w-auto mb-1`}
                                                    onClick={() => action.action()}
                                                >
                                                    {action.icon !== "" ? 
                                                        <div className="flex gap-1 justify-center items-center">
                                                            <span className="h-5 w-5">
                                                                {getIcon({ icon: action.icon })}
                                                            </span>
                                                            {t(action.name, { ns: "modal" })}
                                                        </div>
                                                        :
                                                        t(action.name, { ns: "modal" })
                                                    }
                                                </button>
                                            );
                                        })}
                                    </div>
                                    :
                                    null
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Modal;