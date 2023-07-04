import { QUESTION_TYPE_WORDS } from "@/constants/exam";
import { IInput } from "@/interfaces/form";
import { IRecordStore } from "@/interfaces/store";
import { useRecordStore } from "@/store/record";
import { selectStyle } from "@/styles/select";
import { getFieldByKey } from "@/utils/form";
import { useRouter } from "next/router";
import { PropsWithChildren, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Select from 'react-select'

const WordsVisor : React.FC<PropsWithChildren<{ input: IInput, onChange: any, index: number, onSelectChange: any }>> = ({ children, input, onChange, index, onSelectChange }) => {

    const { t } = useTranslation();     
    const router = useRouter();   

    if (!input || !input.value || !input.value[index]) return null;

    const type = input.value[index].find((item : IInput) => item.name.includes("type"));
    const name = input.value[index].find((item : IInput) => item.name.includes("name"));
    const data = input.value[index].find((item : IInput) => item.name.includes("data"));
    
    if (!type || !type.value || type.value === "") return null;

    const words = type.value.id === QUESTION_TYPE_WORDS ? data.value.split(" ") : data.value;

    return (
        <>
            <div className="grid gap-2 w-full">
                <div className="grid w-full">
                    <span><label>{t(type.label, { ns: "fields" })}</label></span> 
                    <Select 
                        options={type.options}
                        className="focus:outline-none focus:ring-blue-500 focus:border-blue-500 h-10 text-gray-500"
                        styles={selectStyle}
                        defaultValue={type.value}
                        value={type.value}
                        getOptionValue={(option : any) => {                            
                            if (!type.multiple) return option;
                            return option.id;
                        }}
                        getOptionLabel={(option : any) => {
                            return option.display_name ? getFieldByKey(router, option) : t(option.name, { ns: "fields" });
                        }}
                        onChange={(newValue) => onSelectChange(type, newValue)}
                        isDisabled={input.disabled}
                        name={`questions-${index}-type`}
                        //placeholder={t(type.placeholder, { ns: "fields" })}
                        isMulti={input.multiple}
                    />
                </div>
                <div className="grid w-full">
                    <span><label>{t(data.label, { ns: "fields" })}</label></span> 
                    <input 
                        className="w-full h-10 indent-3 border text-gray-500 rounded" 
                        value={data.value}
                        onChange={onChange}
                        name={`questions-${index}-data`}
                        disabled={input.disabled}
                        //placeholder={t(data.placeholder, { ns: "fields" })}
                    />
                </div>
                <div className="max-h-[150px] overflow-y-auto">
                    <div className="grid grid-cols-3 gap-2">
                        {Array.isArray(words) && words.map((word : string, j : number) => {
                            if (!word.length) return "";  

                            return (
                                <div
                                    key={j} 
                                    className="w-full h-10 indent-3 border text-gray-500 flex items-center bg-gray-200 rounded-md" 
                                >
                                    {word}
                                </div>
                            )
                        })}
                    </div>
                    {type.value.id === QUESTION_TYPE_WORDS && words.length > 1 ?
                        <div className="bg-gray-200 absolute bottom-4 left-5 rounded-md p-1 delay-200 ease-in h-8 w-10 cursor-pointer">
                            <div className="text-center w-full h-full hover:animate-bounce cursor-pointer transition delay-700 duration-300 ease-in-out relative">
                                <div className="flex items-center">
                                    {words.length}
                                </div>
                            </div>
                        </div>
                        :
                        null
                    }
                    
                </div>
            </div>
        </>
    );
}


const Visor : React.FC<PropsWithChildren> = ({ children }) => {
    const visorRef = useRef<null | HTMLDivElement>(null);

    // useLayoutEffect(() => {
    //     if (visorRef && visorRef.current) {
    //         visorRef.current.scrollTop = visorRef.current.scrollHeight;
    //     }
    // }, [children]);

    return (
        <>  
            <div ref={visorRef} className='visor shadow-sm border rounded-lg flex-grow h-full bg-gray-200 overflow-y-auto select-none' >
                <span id="text" className='w-full h-full text-black grid justify-center text-4xl break-words p-4 leading-loose'>
                    {children}
                </span>
            </div>
        </>
    )
}


const GridVisor : React.FC<{ words : string }> = ({ words }) => {
    return (
        <>
            <div className={`shadow-sm border border-gray-400 rounded-lg grid grid-cols-12 h-full gap-2 w-full overflow-y-auto select-none p-1 bg-gray-50/80`}>
                {words.split(" ").map(word => {
                    return (
                        <div key={word} className="bg-gray-200 text-black p-1 w-full items-center justify-center grid col-span-3 rounded-md max-h-8 uppercase text-xs sm:text-base">
                            {word}
                        </div>
                    )
                })}
            </div>
        </>
    );
}

const useTyping = () => {
    const SPEED = 40;

    const { setRecord } : IRecordStore = useRecordStore();

    const TextTyping : React.FC<PropsWithChildren<{ string: string }>> = ({ string }) => {

        const [text, setText] = useState<string>("");
        const [index, setIndex] = useState<number>(0);
    
        useEffect(() => {
            if (index < string.length) {    
                setTimeout(() => {
                    setText(text + string[index])
                    setIndex(index + 1)
                }, SPEED);
            }
        }, [index, string, text]);

        useEffect(() => {
            let stop = index === string.length - 1;
            
            if (stop) {
                setRecord!("canStop", true);
            }

            return () => {
                if (stop) stop = true;
            }
        }, [index, string]);

        return <Visor>{text}</Visor>;
    }

    return { TextTyping, Visor, WordsVisor, GridVisor };
}

export default useTyping;