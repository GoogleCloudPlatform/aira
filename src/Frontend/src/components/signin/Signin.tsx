import { ChangeEvent, useState } from "react";
import { useTranslation } from 'next-i18next';
import Image from "next/image";
import { auth } from '@/libs/firebase';
import { useAuth } from "@/context/auth";
import { useSettingsStore } from "@/store/settings";
import { ISettingsStore } from "@/interfaces/store";
import { IInput } from "@/interfaces/form";
import { Auth } from "firebase/auth";
import Language from "../language/Language";

const SignIn : React.FC = () => {
    const { t } = useTranslation();
    const { signIn, signInWithGoogle } = useAuth();
    const { loading } : ISettingsStore = useSettingsStore();

    const [inputs, seIInputs] = useState<IInput[]>([
        { name: 'email', value: '', type: 'text', placeholder: 'Email', label: 'email', required: true, showLabel: true, render: true },
        { name: 'password', value: '', type: 'password', placeholder: 'Password', label: 'password', required: true, showLabel: true, render: true },
    ]);

    const getFieldValue = (fieldName : string) : string => {
        const newInputs = Object.assign([], inputs);

	    const input : (IInput | undefined | any) = newInputs.find((ni : IInput) => ni.name === fieldName);

        if (!input) return "";

        return input.value;
    }

    const handleChange = (event : ChangeEvent<HTMLInputElement>) => {
	    const { name, value } = event.target;

	    const newInputs = Object.assign([], inputs);
	    const input : (IInput | undefined | any) = newInputs.find((ni : IInput) => ni.name === name);
        
        if (!input) return;

        input.value = value;

	    seIInputs(newInputs);
    }

    const validateInputs = () => {
        const email : string = getFieldValue("email");
        const password : string = getFieldValue("password");

        if (!email || !password) return false;

        if (/^\S+@\S+\.\S+$/.test(email) && !['', ' '].includes(password) && password.length >= 5) return true;
        return false;
    }

    const login = async () => {
        if (!validateInputs()) return;

        const email : string = getFieldValue("email");
        const password : string = getFieldValue("password");

        if (!email || !password) return;

        await signIn(email, password);
    }

    const googleLogin = async () => {
        await signInWithGoogle(auth as Auth);
    }
    
    const Divider = () => {    
        return (
            <div>
                <div className="relative flex py-3 items-center">
                    <div className="flex-grow border-t border-gray-200"></div>
                    <div className="flex-grow border-t border-gray-200"></div>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="wrapper flex flex-col w-full h-auto p-8 mt-10 flex-grow">
                <form className="fields h-auto w-full flex flex-col items-center" aria-label="form">
                    {inputs.map(input => 
                        (
                            <div className='mb-3 w-full' key={input.name}>
                                <label className="block text-sm font-bold mb-2" htmlFor={input.name}>
                                    {t(input.name, { ns: 'signin' })}
                                </label>
                                <div className='relative'>
                                    <input       
                                        className="w-full h-10 indent-3 border"                                      
                                        name={input.name}
                                        required
                                        type={input.type} 
                                        placeholder={t(input.label, { ns: 'signin' })} 
                                        onKeyDown={(e) => { e.key === 'Enter' && input.type === 'password' && login() }}
                                        value={input.value}
                                        onChange={(e) => handleChange(e)}
                                        disabled={loading}
                                    />
                                </div>
                            </div>
                        )  
                    )}
                </form>
                <div className="my-4 w-full">
                    <button 
                        className={`
                            w-full md:w-fit h-10 font-bold py-2 px-4 items-center shadow-2xl focus:outline-1 text-white 
                            ${loading || !validateInputs() ? `bg-gray-200 cursor-not-allowed` : ` bg-blue-500  hover:bg-blue-600 cursor-pointer`}
                        `}
                        type="button"
                        onClick={() => login()}
                        //disabled={!validateInputs(inputs) || loading}
                    >
                        {t('signin', { ns: 'signin' })}   
                    </button>
                </div>
                <Divider />
                <button
                    className='bg-white text-gray-500 h-10 shadow mt-10
                                border px-2 py-1 w-full flex items-center 
                                justify-center cursor-pointer
                                hover:bg-gray-50'
                    onClick={() => googleLogin()}
                    disabled={loading}
                >
                    <div className='flex gap-2 items-center w-[180px] justify-between'>
                        <div className='w-[24px] h-[24px] flex items-center justify-center relative'>
                            <Image
                                src="/assets/images/gsignin.png" 
                                alt="google_signin_logo" 
                                fill
                                sizes="(max-width: 768px) 100vw"
                            />
                        </div>
                        <div className='w-[146px] flex items-center justify-center' data-testid='google_signin'>
                            <div className='text-sm font-bold'>{t('signin_with_google', { ns: 'signin' })}</div>
                        </div>
                    </div>
                </button>
                <div className='flex-shrink flex justify-end p-5 absolute bottom-0 right-0'>
                    <Language type="SIGN_IN" />
                </div>
            </div>
        </>
    )
}

export default SignIn;