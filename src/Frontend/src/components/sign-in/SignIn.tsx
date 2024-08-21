'use client';

import { useAuth } from '@/context/auth';
import { auth } from '@/libs/firebase/firebase';
import { Auth } from 'firebase/auth';
import { useTranslations } from 'next-intl';
import { Separator } from '../ui/separator';
import { Button } from '../ui/button';
import FormSignIn from '@/forms/signin/FormSignIn';

const SignIn : React.FC = () => {    

    const t = useTranslations('form.signin');
    const { signInWithGoogle } = useAuth();

    const googleLogin = async () => await signInWithGoogle(auth as Auth);

    return (
        <>
        
            <div className="w-full h-fit p-5 gap-5">
                <FormSignIn />
     
                <Separator className='bg-border dark:bg-darkBorder my-6' />

                <Button 
                    data-testid='google_signin'
                    type="button" 
                    className="w-full h-9 text-white focus:ring-1 focus:outline-none focus:ring-primary/50 font-medium rounded-md text-sm px-5 py-2.5 text-center inline-flex items-center justify-center dark:focus:ring-darkPrimary/55"
                    onClick={() => googleLogin()}
                >
                    <svg className="w-4 h-4 mr-2 -ml-1" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512"><path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path></svg>
                    {t("button_google_sign_in")}
                </Button>
            </div>
        </>
    );
}

export default SignIn;