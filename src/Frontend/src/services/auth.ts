import Alert from '@/classes/Alert';
import { api } from '@/pages/api/api';
import { IAuthSigninResponse } from '@/interfaces/auth';
import { onAuthStateChanged, User, GoogleAuthProvider, signInWithPopup, UserCredential, Auth } from 'firebase/auth';
import { ENDPOINT_AUTH_REFRESH, ENDPOINT_AUTH_TOKEN } from '@/constants/endpoint';
import { ALERT_ERROR } from '@/constants/alert';

const AlertInstance = new Alert();

export async function signIn(email: string, password: string) : Promise<IAuthSigninResponse | null> {
    return new Promise<IAuthSigninResponse | null>((resolve, reject) => {
        try {
            const bodyData = {
                email_address: email,
                password
            }

            api.post(ENDPOINT_AUTH_TOKEN, bodyData).then(response => {        
                const { id, access_token, refresh_token, token_type, scopes, user_name } = response.data;
    
                resolve({ 
                    id,
                    access_token, 
                    refresh_token,
                    token_type,
                    scopes,
                    email,
                    user_name
                });
            }).catch((error : any) => {
                if (process.env.NODE_ENV === 'development') console.error('REQUEST ERROR :' + error);                        
                AlertInstance.alert(ALERT_ERROR, 'error_auth');
                reject(null);
            })
           
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });            
}

export async function googleSignIn(firebaseAuth : Auth) : Promise<IAuthSigninResponse | null> {
    return new Promise<IAuthSigninResponse | null>(async (resolve, reject) => {
        try {
            // Sign in using a popup.
            const provider = new GoogleAuthProvider();
            provider.setCustomParameters({ prompt:'select_account' });        
            provider.addScope('profile');

            const result : (UserCredential | void) = await signInWithPopup(firebaseAuth, provider).catch(error => {
                if (process.env.NODE_ENV === 'development') console.error('FIREBASE GOOGLE AUTH ERROR: ' + error);
                AlertInstance.alert(ALERT_ERROR, "error_google_auth")
                reject(null);
            });
            
            if (!result) return reject(null);
            const user : (User | any) = result.user;
            const { email } = user;

            const bodyData = { token: user.accessToken };
            
            await api.post(ENDPOINT_AUTH_TOKEN, bodyData).then(response => {
                const { id, access_token, refresh_token, token_type, scopes, user_name } = response.data;
    
                resolve({ 
                    id,
                    access_token, 
                    refresh_token,
                    token_type,
                    scopes,
                    email,
                    user_name
                });
            }).catch((error : any) => {
                if (process.env.NODE_ENV === 'development') console.error('REQUEST ERROR :' + error);                        
                AlertInstance.alert(ALERT_ERROR, 'error_auth');
                reject(null);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function refreshToken(firebaseAuth: Auth) : Promise<IAuthSigninResponse | null> {
    return new Promise<IAuthSigninResponse | null>(async (resolve, reject) => {
        try {
            onAuthStateChanged(firebaseAuth, async (user) => {
                const userStorage : (string | null) = localStorage.getItem('user');
                const access_token : (string | null) = localStorage.getItem('token');
                const refresh_token : (string | null) = localStorage.getItem("refresh_token");
                if (!access_token || !userStorage || !refresh_token) return reject(null);

                api.post(ENDPOINT_AUTH_REFRESH, {}).then(response  => {
                    const { id, access_token, refresh_token, token_type, scopes } = response.data;

                    if (!id){
                        AlertInstance.alert(ALERT_ERROR, 'error_no_data');
                        resolve(null);
                    }

                    resolve({ 
                        id,
                        access_token, 
                        refresh_token,
                        token_type,
                        scopes,
                        email: JSON.parse(userStorage).email,
                        user_name: JSON.parse(userStorage).user_name
                    });
                }).catch((error: any) => {
                    AlertInstance.alert(ALERT_ERROR, 'error_api');
                    if (process.env.NODE_ENV === 'development') console.error('API ERROR REFRESHING TOKEN: ' + error);
                    reject(null);
                });                
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(null);
        }
    })
}