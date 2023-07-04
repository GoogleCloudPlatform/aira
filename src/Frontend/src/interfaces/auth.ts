import { Auth } from "firebase/auth";

export interface IUser {
    id: string;
    email?: string;
    name?: string;
    scopes?: Array<string>;
    user_name?: string;
}

export interface IAuthSigninResponse {
    id: string,
    access_token: string;
    scopes: Array<string>;
    refresh_token: string;
    token_type: string;
    email: string;
    user_name: string;
}

export interface IAuthRefreshToken {
    access_token: string;
}

export interface IAuthContext {
    authenticated: boolean;
    user: IUser | null;
    loading: boolean,
    signOut(): Promise<void>;
    signIn(email: string, password: string): Promise<void>;
    signInWithGoogle(firebaseAuth : Auth) : Promise<void>;
}

export interface IProfileResponse {
    
}