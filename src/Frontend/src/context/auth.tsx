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
import { createContext, useContext, useEffect, useState, PropsWithChildren, ReactNode } from "react";
import { useRouter } from "next/router";
import { IAuthContext, IAuthSigninResponse, IUser } from '@/interfaces/auth';
import { api } from "@/pages/api/api";
import * as auth from '@/services/auth';
import * as NextError from "next/error";
import { SplashScreen } from "@/components";
import { ISettingsStore } from "@/interfaces/store";
import { useSettingsStore } from "@/store/settings";
import { ROUTES_ALLOWED_PATHS, ROUTES_SIGNED_PATHS, ROUTES_SIGNED_PATHS_PARAMS } from "@/constants/routes";
import { Auth } from "firebase/auth";
import { getProfile } from "@/services/users";


type TAuthProvider = {
    children: ReactNode
}

const AuthContext = createContext<IAuthContext>({} as IAuthContext);

const AuthProvider: React.FC<TAuthProvider> = ({ children } : PropsWithChildren<{}>) => {
    const router = useRouter();   

    const settingsStore : ISettingsStore = useSettingsStore();
    const { loading, setSettings } = settingsStore;

    const [user, setUser] = useState<IUser | null>(null);
    const [mounted, setMounted] = useState<boolean>(false);

    useEffect(() => {
        setMounted(true);
        return () => {
            setMounted(false);
            setSettings("loading", false);
        }
    }, [setSettings]);

    useEffect(() => {               
        const loadStorageData = async () => {    
            const storageUser = await localStorage.getItem('user');
            const storageToken = await localStorage.getItem("token");
    
            if (storageUser && storageToken) {
                setUser(JSON.parse(storageUser));
                api.defaults.headers.common['Authorization'] = `Bearer ${storageToken}`;
            }
        }

        loadStorageData();
    }, []);

    const handleAuthentication = async (response : IAuthSigninResponse) => {
        const { id, access_token, refresh_token, scopes, email, user_name } = response;

        if (!id) return;        

        // const profile = await getProfile();
        // if (!profile) return;

        const user : IUser = { id: id, scopes, email, user_name };

        await localStorage.setItem('user', JSON.stringify(user));
        await localStorage.setItem('token', access_token); 
        await localStorage.setItem('refresh_token', refresh_token); 
        
        setUser(user);     
                
        return router.push("/home");
    }

    const signIn = async (email: string, password: string) => {
        try {
            settingsStore.toggleLoading?.();

            const response = await auth.signIn(email, password);

            if (!response) return settingsStore.toggleLoading?.();

            handleAuthentication(response).then(() => settingsStore.toggleLoading?.());
        } catch (error) {
            if (process.env.NODE_ENV === 'development') console.error(error);
            settingsStore.toggleLoading?.();
        }
    } 

    const signInWithGoogle = async (firebaseAuth : Auth) => {
        try {
            settingsStore.toggleLoading?.();
            
            const response = await auth.googleSignIn(firebaseAuth);          

            if (!response) return settingsStore.toggleLoading?.();

            handleAuthentication(response).then(() => settingsStore.toggleLoading?.());
        } catch (error) {
            if (process.env.NODE_ENV === 'development') console.error(error);
            settingsStore.toggleLoading?.();
        }
    }

    const signOut = async () => {
        router.push('/signin');
        await localStorage.clear();
        setUser(null);
    }
  

    if (!mounted) return <SplashScreen />;

    return (
        <AuthContext.Provider value={{ authenticated: !!user, user, loading, signIn, signOut, signInWithGoogle }}>
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

const ProtectRoute = ({ children } : any) => {
    const { authenticated } = useAuth();
    
    const allowedPaths = [...ROUTES_ALLOWED_PATHS];

    // new routes should be added here
    const signedPaths = [...ROUTES_SIGNED_PATHS];

    const signedPathsWithParams = [...ROUTES_SIGNED_PATHS_PARAMS];

    let checkPaths = false;    
    let checkAllowedPaths = false;
    let checkSignedPaths = false;
    
    if (typeof window !== "undefined") {
        
        const containsWildcard = signedPathsWithParams.some(path => {
            const regexPattern = new RegExp('^' + path.replace(/:[^/]+/g, '[^/]+') + '$');
            return regexPattern.test(window.location.pathname);
        });

        if (allowedPaths.includes(window.location.pathname) || signedPaths.includes(window.location.pathname) || containsWildcard) checkPaths = true;
        if (allowedPaths.includes(window.location.pathname)) checkAllowedPaths = true;
        if (signedPaths.includes(window.location.pathname) || containsWildcard) checkSignedPaths = true;        

        if (!checkPaths) return <NextError.default statusCode={404} title={"Page Not Found"} />
    
        if (!authenticated && checkSignedPaths) return <NextError.default statusCode={403} title={"Unauthorized"} />

        return children;
    }

    return null;    
};

export { AuthProvider, useAuth, ProtectRoute };