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