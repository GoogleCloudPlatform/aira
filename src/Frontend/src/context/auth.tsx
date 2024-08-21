'use client';

import { Auth } from "firebase/auth";
import { createContext, useContext, useEffect, useState, PropsWithChildren, ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { IAuthContext, IAuthSigninResponse, IUser } from '@/interfaces/auth';
import { api } from "@/api/api";
import * as auth from '@/services/auth';
import { clearCookie, getCookie, setCookie } from "@/utils/auth";
import { useLoading } from "./loading";
import { ROUTES_ALLOWED_PATHS } from "@/constants/routes";

type TAuthProvider = {
    children: ReactNode
}

const AuthContext = createContext<IAuthContext>({} as IAuthContext);

const AuthProvider: React.FC<TAuthProvider> = ({ children } : PropsWithChildren<{}>) => {
    const router = useRouter();   
    const { loading, setLoading } = useLoading();

    const [user, setUser] = useState<IUser | null>(null);
    const [mounted, setMounted] = useState<boolean>(false);

    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
            setLoading(false);
        }
    }, [setLoading]);

    useEffect(() => {               
        const loadStorageData = async () => {    
            const cookiedUser = getCookie('user');
            const cookiedToken = getCookie('token');
    
            if (cookiedUser && cookiedToken) {
                setUser(JSON.parse(cookiedUser));
                api.defaults.headers.common['Authorization'] = `Bearer ${cookiedToken}`;
            }
        }

        loadStorageData();
    }, []);

    /**
     * Handles authentication based on the response from a sign-in request.
     * Extracts necessary information from the response, sets cookies, updates user state,
     * and redirects the user to the home page upon successful authentication.
     * @param {IAuthSigninResponse} response - The response object received from the sign-in request.
     * @returns {Promise<void>} - A promise resolving when authentication handling is complete.
     */
    const handleAuthentication = async (response : IAuthSigninResponse) => {
        const { id, access_token, refresh_token, scopes, email, user_name, user_id } = response;

        if (!id) return;        

        const user : IUser = { id: id, scopes, email, user_name, user_id };

        setCookie('user', JSON.stringify(user)); 
        setCookie('token', access_token); 
        setCookie('refresh_token', refresh_token); 

        setUser(user);
                
        return router.push("/home");
    }

    const signIn = async (email: string, password: string) => {
        try {
            setLoading(true);

            const response = await auth.signIn(email, password);

            if (!response) return;

            handleAuthentication(response);
        } catch (error) {
            if (process.env.NODE_ENV === 'development') console.error(error);
        } finally {
            setLoading(false)
        }
    } 

    const signInWithGoogle = async (firebaseAuth : Auth) => {
        try {
            setLoading(true);
            const response = await auth.googleSignIn(firebaseAuth);          

            if (!response) return;

            handleAuthentication(response);
        } catch (error) {
            if (process.env.NODE_ENV === 'development') console.error(error);
        } finally {
            setLoading(false)
        }
    }

    const signOut = async () => {
        router.push('/')
        localStorage.clear();
        clearCookie("user");
        clearCookie("token");
        clearCookie("refresh_token");
        setUser(null);
    }
  

    if (!mounted) return null;

    return (
        <AuthContext.Provider value={{ authenticated: !!user, user, signIn, signOut, signInWithGoogle }}>
            {children}
        </AuthContext.Provider>
    );
};

const useAuth = () => {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider.');
    }

    return context;
}

const PrivateRoute : React.FC<PropsWithChildren> = ({ children }) => {
    const { authenticated, user } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const params = useSearchParams();
    
    const isAllowed = ROUTES_ALLOWED_PATHS.includes(pathname);
    const isResetRoute = pathname.includes('/reset');
    const hasResetToken = params.get("token");
    const isResetPassword = isResetRoute && hasResetToken

    useEffect(() => {
        if ((!authenticated || !user) && !isResetPassword) {
            console.warn("[AUTH]: unauthorized. Redirecting...");
            router.push("/");
        }
    }, [authenticated, user, router, isResetPassword]);

    // allowed paths should render page anyway
    if (isResetPassword) return children;
    if (isAllowed) return children;

    return authenticated ? children : null;
};

export { PrivateRoute, AuthProvider, useAuth };