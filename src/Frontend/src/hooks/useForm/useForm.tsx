import { ICON_LANGUAGE, ICON_TABLE_CELLS, ICON_TRASH, ICON_X_MARK } from "@/constants/icons";
import { IDependence, IInput, IOption } from "@/interfaces/form";
import { useFormStore } from "@/store/form";
import { isEmpty, isObject } from "lodash";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import useIcon from "../useIcon/useIcon";
import { useRouter } from "next/router";
import { getFieldByKey } from "@/utils/form";
import useTyping from "../useTyping/useTyping";
import useClickOutside from "../useClickOutside/useClickOutside";
import Select from 'react-select'
import { selectStyle } from "@/styles/select";
import { QUESTION_TYPE_WORDS } from "@/constants/exam";

const useForm = () => {
    const popupRef = useRef<HTMLDivElement>(null);
    const [showPopup, setShowPopup] = useState<boolean>(false);
    const [valueIndex, setValueIndex] = useState<number>(0);

    const router = useRouter();
    const { inputs, getForm, setForm } = useFormStore();
    const { t } = useTranslation();
    const { getIcon } = useIcon();
    const { WordsVisor } = useTyping();

    const { locale } = router;

    useEffect(() => {
        return () => setShowPopup(false);
    }, []);

    useClickOutside(popupRef, () => setShowPopup(false));

    const checkFormSubmit = () => {
        try {
            const form = getForm();
            let shouldSubmit = false;

            const dates = form.inputs.filter((item : IInput) => ["start_date", "end_date"].includes(item.name));
            
            if (dates && dates.length) {
                const start_date = dates.find((item : IInput) => item.name === "start_date");
                const end_date = dates.find((item : IInput) => item.name === "end_date");
    
                if (!start_date && !end_date) return false;
    
                const startDate = new Date(start_date?.value);
                const endDate = new Date(end_date?.value);
    
                if (endDate < startDate) {
                    toast.warning(t('warning_fill_form_dates', { ns: "toast" }));
                    return true;
                }
            }

            let shouldStop = false;

            outerInputs: for (let i = 0; i < form.inputs.length; i++) {    
                
                const input = form.inputs[i];

                if (!input.required) continue;
                
                shouldSubmit = !isEmpty(input.value) ? true : false;
                if (!shouldSubmit) break;

                const dependencies = input.dependencies || [];
                for (let k = 0; k < dependencies.length; k++) {
                    const dependency = dependencies[k];
                    if (dependency) {
                        let conditionValue = input.value;
                        
                        if (input.value.display_name) { 
                            conditionValue = input.value.display_name[locale as string];
                        }

                        const hasDependency = dependency.condition_values?.includes(conditionValue) ? true : false;
                        const hasDependencyValue = form.inputs.some((field : IInput) => field.name === dependency.key && isEmpty(field.value));
                        if (hasDependencyValue && hasDependency) {
                            toast.warning(t('warning_missing_fields', { ns: "toast" }));
                            shouldStop = true;
                            shouldSubmit = false;
                            break outerInputs;
                        }
                    } 
                };
                
    
                if (input.type === "array") {
                    if (input.value.length) {
                        for (let j = 0; j < input.value.length; j++) {
                            shouldStop = input.value[j].some((inp : IInput) => inp.value.length === 0)
                            if (shouldStop) {
                                toast.warning(t('warning_fill_form_questions', { ns: "toast" }));
                                shouldSubmit = false;
                                break outerInputs
                            } 
                        }
                    } else {
                        shouldSubmit = false;
                        break;
                    }
                }

                if (input.type === "password") {
                    if (input.value.length <= 4) {
                        toast.warning(t('warning_short_password', { ns: "toast" }));
                        return true;
                    }

                    const confirmPassword = form.inputs.find((field : IInput) => field.name === "confirm_password");
                    if (confirmPassword && input.value !== confirmPassword.value) {
                        toast.warning(t('warning_password_not_match', { ns: "toast" }));
                        return true;
                    }
                }

                if (input.type === "email") {
                    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    const isValid = emailPattern.test(input.value);
                    if (!isValid) {
                        toast.warning(t('warning_fill_form_email', { ns: "toast" }));
                        return true;
                    }                        
                }            
            }
            
            if (!shouldSubmit && !shouldStop) toast.warning(t('warning_fill_form', { ns: "toast" }));
    
            return !shouldSubmit;
        } catch (error) {
            console.error(error);
            toast.error(t('error_fill_form', { ns: "toast" }));
            return true;
        }
       
    }

    const handleChange = useCallback((event : React.FormEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = event.currentTarget;

        const [fieldName, index, key] = name.split("-");

        const newInputs = Object.assign([], inputs);
        const newInput : IInput | undefined | any = newInputs.find((i : IInput) => i.name === fieldName);
        
        if (!newInput) return null;
        
        if (newInput.type === 'array') {
            const newData = newInput.value[index].find((item : any) => item.name.includes(key));
            newData.value = value;
        } else if (type === 'select-multiple') {
            if (newInput.value.includes(value)) newInput.value = newInput.value.filter((item : string) => item !== value);
            else newInput.value.push(value);
        } else if (type === 'date') {
            newInput.value = value;
        } else { 
            newInput.value = value;
        }

        // check if field has to hide/show another field
        const dependencies = newInput.dependencies || [];
        newInputs.forEach((field : IInput) => {
            const dependency : IDependence = dependencies.find((dep : IDependence) => dep.key === field.name);
            if (!dependency) return;
            const conditionValue = value;
            const hasDependency = dependency.condition_values?.includes(conditionValue) ? true : false;
            field.render = hasDependency;
            field.required = hasDependency;
        });

        setForm("inputs", newInputs);

    }, [inputs, setForm]);


    const handleSelectChange = (input: IInput, newValue : any) => {
        const { name } = input;

        const [fieldName, index, key] = name.split("-");

        const newInputs : Array<IInput> = Object.assign([], inputs);

        const newInput = newInputs.find((i : IInput) => i.name === fieldName);
        if (!newInput) return;

        if (key) { // used for questions fields only
            newInput.value[index] = newInput.value[index].map((i : any) => {
                if (i.name.includes(key)) {
                    return { ...i, value: newValue };
                }
                return i;
            });
        } else {
            (newInput as IInput).value = newValue;
        }

        // check if field has to hide/show another field
        const dependencies = input.dependencies || [];
        newInputs.forEach((field) => {
            const dependency : IDependence | undefined = dependencies.find((dep : IDependence) => dep.key === field.name);
            if (!dependency) return;

            
            // reset field options
            field.options = field.defaultOptions;
            if (!Array.isArray(newValue)) field.value = [];
            if (isEmpty(newValue)) field.value = [];

            Array.isArray(field.value) && field.value.map((fv : any) => {
                newValue.map((nv : any) => {
                    if (nv.id !== fv["organization"].id && !newValue.some((i : any) => i.id === fv["organization"].id)) {
                        field.value = field.value.filter((ff : any) => ff.id !== fv.id);
                    }
                })
            });
            

            if (dependency.dynamic) {
                if (isEmpty(field.options) || isEmpty(newValue)) return;
                const conditionValue = Array.isArray(newValue) ? newValue : newValue.id;
                let newOptions : any = [];
                if (Array.isArray(newValue)) {
                    newValue.map((v) => {
                        return field.defaultOptions.map((o : any) => {
                            if (o["organization"].id === v.id) newOptions.push(o);
                        });
                    });
                } else {
                    newOptions = field.defaultOptions.filter((option : any) => option["organization"].id === conditionValue);
                }

                if (isEmpty(newOptions)) {
                    toast.warning(t(`warning_no_${field.name}`, { ns: "toast" }));
                }
                
                field.options = newOptions;
            } 
            
            if (dependency.condition_values){
                let conditionValue = field.value;
                
                if (newValue.display_name) {
                    conditionValue = newValue.display_name[locale as string];
                }
                
                const hasDependency = dependency.condition_values?.includes(conditionValue) ? true : false;
                field.render = hasDependency;
                field.required = hasDependency;
                field.multiple = dependency.condition_multiple ? dependency.condition_multiple?.includes(conditionValue) : field.multiple;
                field.disabled = newValue.id ? false : true;
                field.value = [];
            }
            
        
        });

        setForm("inputs", newInputs);
    }

    const addItem = (input : IInput) => {
        const newInputs = Object.assign([], inputs);
        const newInput : IInput | undefined | any = newInputs.find((i : IInput) => i.name === input.name);

        if (!newInput) return null;

        const newValue = Object.assign([], newInput.value);
        const newField = Object.assign([], newInput.fields);

        const mappedArray = newField.map((item : any) => {
            const name = item.name.replace("0", newValue.length);
            return {
                ...item,
                name: name,
                value: item.type === "select" ? { id: item.value, name: item.value, value: item.value } : item.value
            };
        });

        newValue.push(mappedArray);
        newInput.value = newValue;

        setForm("inputs", newInputs);        
    }


    const removeItem = (input : IInput, index : number) => {
        const newInputs = Object.assign([], inputs);
        const newInput : IInput | undefined | any = newInputs.find((i : IInput) => i.name === input.name);

        if (!newInput) return null;
        newInput.value.splice(index, 1);
        
        setForm("inputs", newInputs);        
    }


    const openPopup = (index : number) => {
        setShowPopup(true);
        setValueIndex(index)
    }

    const createInput = (input : IInput, index : number) => {
        if (!input || !input.render) return null;

        const { name, type, value, label, placeholder, options, required, multiple, fields, classes, disabled, showLabel, onChange } = input;

        if (type === "radio") {
            if (!options || isEmpty(options)) return null;

            return (
                <div key={index}>
                    {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                    <ul className="items-center w-full text-gray-500 bg-white border border-gray-200 rounded-lg sm:flex">
                        {options.map((option : IOption) => {
                            return (
                                <li key={option.id} className="w-full border-b border-gray-200 sm:border-b-0 sm:border-r">
                                    <div className="flex items-center pl-3">
                                        <input 
                                            id={option.name}
                                            type={type}
                                            value={option.value} 
                                            name={`${name}-${index}`} 
                                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
                                            onChange={handleChange} 
                                            placeholder={t(placeholder, { ns: "fields" })} 
                                            required={required}
                                            disabled={disabled}
                                        />
                                        <label 
                                            htmlFor={option.name}
                                            className="w-full py-3 ml-2 text-gray-500"
                                        >
                                            {t(option.name, { ns: "fields" })}
                                        </label>
                                    </div>
                                </li>
                            )    
                        })}
                    </ul>
                </div>
            );
        }

        if (type === "select") {
            if (!options || isEmpty(options)) return null;

            return (
                <div key={index}>
                    {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                    <Select 
                        name={`${name}-${index}`} 
                        options={options} 
                        defaultValue={value}
                        getOptionValue={(option) => {
                            if (!multiple) return option;
                            return option.id;
                        }}
                        getOptionLabel={(option) => {
                            return option.display_name ? getFieldByKey(router, option) : t(option.name, { ns: "fields" });
                        }}
                        className="focus:outline-none focus:ring-blue-500 focus:border-blue-500 h-10 text-gray-500 text-left"
                        styles={selectStyle}
                        isMulti={multiple}
                        placeholder={t(placeholder, { ns: "fields" })}
                        value={value}
                        required={required}
                        isDisabled={disabled}
                        onChange={(newValue) => handleSelectChange(input, newValue)}
                    />
                </div>    
            )
        }

        if (type === "object") {
            if (!locale) return null;

            return (
                <div key={index}>
                    <div className="flex flex-col w-full h-full gap-1">
                        {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                        <input 
                            className="w-full h-10 indent-3 border text-gray-500 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
                            name={`${name}-${index}`} 
                            type={type} 
                            value={value[locale]} 
                            onChange={handleChange} 
                            // placeholder={t(placeholder, { ns: "fields" })} 
                            required={required}
                            disabled={disabled}
                        />
                    </div>
                </div>
            )
        }

        if (type === "date") {
            return (
                <div key={index}>
                    <div className={`item ${classes ? classes : ""}`}>
                        {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                        <input 
                            className="w-full h-10 indent-1 border text-gray-500 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
                            name={`${name}-${index}`} 
                            type={type} 
                            value={value} 
                            onChange={handleChange} 
                            placeholder={t(placeholder, { ns: "fields" })} 
                            required={required}
                            disabled={disabled}
                        />
                    </div>
                </div>
            );  
        }

        if (type === "datetime-local") {
            return (
                <div key={index}>
                    <div className={`item ${classes ? classes : ""}`}>
                        {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                        <input 
                            className="w-full h-10 indent-1 border text-gray-500 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
                            name={`${name}-${index}`} 
                            type={type} 
                            value={value} 
                            onChange={handleChange} 
                            placeholder={t(placeholder, { ns: "fields" })} 
                            required={required}
                            disabled={disabled}
                        />
                    </div>
                </div>
            );  
        }

        if (type === "array") {
            if (!fields) return null;

            return (
                <>
                    <div key={index}>
                        <div className="flex flex-col w-full h-full gap-1">
                            {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                            <div className="w-full h-full indent-3 border text-gray-400 rounded">
                                <div className="p-2 overflow-y-auto max-h-[80px] md:max-h-[300px]">
                                    {Array.isArray(value) && value.length ? value.map((field : any, index: number) => (
                                        <div key={index} className="flex gap-2 border p-2 bg-gray-50 mb-2">
                                            {isObject(field) ? 
                                                <div className={`w-full grid ${!input.disabled ? 'grid-cols-12': 'grid-col-5'} items-center`}>
                                                    {Object.keys(field).map((k: string, i: number) => {
                                                        
                                                        const fieldEntries : any = field[k as keyof typeof field];
                                                        const { type, value } = fieldEntries;

                                                        if (!fieldEntries?.name || !fieldEntries.name.includes("name")) return null;

                                                        return (
                                                            <div key={k} className="w-full grid grid-flow-col grid-cols-5 col-span-11 items-center">
                                                                <div className="col-span-4">
                                                                    {createInput(field[k as keyof typeof field], index)}
                                                                </div>
                                                                <div className="col-span-1 justify-center grid">
                                                                    <button 
                                                                        className="w-8 h-8 bg-gray-200 sm:shadow-lg rounded-md p-2 hover:bg-gray-300"
                                                                        onClick={() => openPopup(index)}
                                                                        type="button"
                                                                    >
                                                                        <div className="w-4 h-4">
                                                                            {value === QUESTION_TYPE_WORDS ? 
                                                                                getIcon({ icon: ICON_TABLE_CELLS, classes: "text-blue-500" })
                                                                                :
                                                                                getIcon({ icon: ICON_LANGUAGE, classes: "text-blue-500" }) 
                                                                            }
                                                                        </div>
                                                                    </button>
                                                                        
                                                                        
                                                                            
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                    {!input.disabled ? 
                                                        <div className="grid col-span-1 justify-center h-full items-center">
                                                            <button 
                                                                className="w-8 h-8 bg-gray-200 sm:shadow-lg rounded-md p-2 hover:bg-gray-300"
                                                                onClick={() => removeItem(input, index)}
                                                                type="button"
                                                            >
                                                                <div className="w-4 h-4">
                                                                    {getIcon({ icon: ICON_TRASH, classes: "text-red-500 hover:text-red-600" })}
                                                                </div>
                                                            </button>
                                                        </div>
                                                        :
                                                        null
                                                    }
                                                </div>
                                                : 
                                                null
                                            }
                                        </div>
                                    ))
                                        :
                                        <div className="flex justify-center items-center p-1 md:p-5 w-full h-full overflow-x-hidden overflow-y-auto">
                                            {t("no_items", { ns: "fields" })}
                                        </div>
                                    }
                                </div>
                                <div className="p-1 sm:p-0">
                                    {!input.disabled ? 
                                        <button 
                                            type="button" 
                                            className="flex mt-2 w-full sm:w-fit h-fit justify-center rounded-md px-3 py-2 text-sm font-semibold shadow-sm bg-green-600 text-white hover:bg-green-700 sm:absolute sm:bottom-4 sm:left-5"
                                            onClick={() => addItem(input)}
                                        >
                                            {t("add_question", { ns: "fields" })}
                                        </button>
                                        :
                                        null
                                    }
                                </div>
                                {showPopup ? 
                                    <>
                                        <div className="relative z-20" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                                            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity">
                                                <div className="fixed inset-0 z-20 overflow-y-auto">
                                                    <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
                                                        <div ref={popupRef} className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 w-full sm:max-w-lg">
                                                            <div className="absolute p-2 top-0 right-0">
                                                                <button onClick={() => setShowPopup(false)} className="w-5 h-5">
                                                                    {getIcon({ icon: ICON_X_MARK, classes: "text-gray-300" })}
                                                                </button>
                                                            </div>
                                                            <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                                                <div className="sm:flex sm:items-start p-2">
                                                                    <WordsVisor 
                                                                        input={input} 
                                                                        onChange={handleChange}
                                                                        index={valueIndex}
                                                                        onSelectChange={handleSelectChange}
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 gap-2">
                                                                <button  
                                                                    className={`flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold shadow-sm sm:ml-3 sm:w-auto mb-1 bg-blue-500 text-white`}
                                                                    onClick={() => setShowPopup(false)}
                                                                    type="button"
                                                                >
                                                                    {t("ok", { ns: "fields" })}
                                                                </button>    
                                                                <button 
                                                                    className={`inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold shadow-sm sm:ml-3 sm:w-auto mb-1 text-black`}
                                                                    onClick={() => setShowPopup(false)}
                                                                    type="button"
                                                                >
                                                                    {t("close", { ns: "fields" })}
                                                                </button>    
                                                    
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </> 
                                    : 
                                    null
                                }
                            </div>
                        </div>
                    </div>
                </>
            );
        }

        return (
            <div key={index}>
                <div className={`item ${classes ? classes : ""}`}>
                    {showLabel ? <span><label>{t(label, { ns: "fields" })}</label></span> : null}
                    <input 
                        className="w-full h-10 indent-3 border text-gray-500 rounded focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
                        name={`${name}-${index}`} 
                        type={type} 
                        value={value} 
                        onChange={handleChange} 
                        placeholder={t(placeholder, { ns: "fields" })} 
                        required={required}
                        disabled={disabled}
                    />
                </div>
            </div>
        );        
    }


    const RenderInputs : React.FC<any> = ({ inputs }) : any => {

        if (!Array.isArray(inputs)) return null;

        return (
            <>
                {inputs.map((input : IInput, index : number) => {
                    return (
                        <div key={index}>
                            {createInput(input, index)}
                        </div>
                    );
                })}
            </>  
        );
    }

    return { inputs, setForm, createInput, RenderInputs, checkFormSubmit };
}

export default useForm;