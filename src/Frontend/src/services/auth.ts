import Alert from '@/classes/Alert';
import { api } from '@/api/api';
import { IAuthSigninResponse } from '@/interfaces/auth';
import { onAuthStateChanged, User, GoogleAuthProvider, signInWithPopup, UserCredential, Auth, signInWithCredential } from 'firebase/auth';
import { ENDPOINT_AUTH_FORGOT_PASSWORD, ENDPOINT_AUTH_REFRESH, ENDPOINT_AUTH_RESET, ENDPOINT_AUTH_TOKEN } from '@/constants/endpoints';
import { ALERT_ERROR, ALERT_SUCCESS } from '@/constants/alerts';
import { getCookie } from '@/utils/auth';

const AlertInstance = new Alert();

export async function signIn(email: string, password: string) : Promise<IAuthSigninResponse | null> {
    return new Promise<IAuthSigninResponse | null>((resolve, reject) => {
        try {
            const bodyData = {
                email_address: email,
                password
            }

            api.post(ENDPOINT_AUTH_TOKEN, bodyData).then(response => {        
                const { id, access_token, refresh_token, token_type, scopes, user_name, user_id } = response.data;
                resolve({ 
                    id,
                    access_token, 
                    refresh_token,
                    token_type,
                    scopes,
                    email,
                    user_name,
                    user_id
                });
            }).catch(e => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.auth.error_auth');
                if (process.env.NODE_ENV === 'development') console.error('[REQUEST ERROR]: ' + e);
                reject(null);
            });
        } catch (e) {
            AlertInstance.alert(ALERT_ERROR, 'toast.errors.auth.error_auth');
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
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
                if (process.env.NODE_ENV === 'development') console.error('[FIREBASE GOOGLE AUTH ERROR]: ' + error);
                AlertInstance.alert(ALERT_ERROR, "error_google_auth")
                reject(null);
            });
            
            if (!result) return reject(null);
            const user : (User | any) = result.user;
            const { email } = user;

            const bodyData = { token: user.accessToken };
            
            await api.post(ENDPOINT_AUTH_TOKEN, bodyData).then(response => {
                const { id, access_token, refresh_token, token_type, scopes, user_name, user_id } = response.data;
    
                resolve({ 
                    id,
                    access_token, 
                    refresh_token,
                    token_type,
                    scopes,
                    email,
                    user_name,
                    user_id
                });
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR]: ' + e);
            AlertInstance.alert(ALERT_ERROR, 'toast.errors.auth.error_auth');
            reject(null);
        }
    });
}

export async function refreshToken(firebaseAuth: Auth) : Promise<IAuthSigninResponse | null> {
    return new Promise<IAuthSigninResponse | null>(async (resolve, reject) => {
        try {
            onAuthStateChanged(firebaseAuth, async (user) => {
                const userStorage : (string | null) = getCookie('user');
                const access_token : (string | null) = getCookie('token');
                const refresh_token : (string | null) = getCookie("refresh_token");
                if (!access_token || !userStorage || !refresh_token) return reject(null);

                api.post(ENDPOINT_AUTH_REFRESH, {}).then(response  => {
                    const { id, access_token, refresh_token, token_type, scopes, user_id } = response.data;

                    if (!id){
                        AlertInstance.alert(ALERT_ERROR, 'toast.errors.error_no_data');
                        resolve(null);
                    }

                    resolve({ 
                        id,
                        access_token, 
                        refresh_token,
                        token_type,
                        scopes,
                        email: JSON.parse(userStorage).email,
                        user_name: JSON.parse(userStorage).user_name,
                        user_id
                    });
                }).catch((error: any) => {
                    AlertInstance.alert(ALERT_ERROR, 'toast.errors.auth.error_api');
                    if (process.env.NODE_ENV === 'development') console.error('[API ERROR REFRESHING TOKEN]: ' + error);
                    reject(null);
                });                
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('[PROMISE ERROR REFRESHING TOKEN]: ' + e);
            reject(null);
        }
    })
}

export async function forgotPassword(email : string) : Promise<Boolean> {
    return new Promise<Boolean>(async (resolve, reject) => {
        try {
            api.post(ENDPOINT_AUTH_FORGOT_PASSWORD, { email }).then(response => {
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.auth.forgot_password_email_sent');
                resolve(true);
            }).catch((error: any) => {
                AlertInstance.alert(ALERT_ERROR, 'toast.errors.auth.error_api');
                if (process.env.NODE_ENV === 'development') console.error('API ERROR FORGOT PASSWORD: ' + error);
                reject(false);
            });                
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(false);
        }
    });
}

export async function resetPassword(token : string, password : string) : Promise<Boolean> {
    return new Promise<Boolean>(async (resolve, reject) => {
        try {
            api.post(ENDPOINT_AUTH_RESET, { token, password }).then(response => {
                AlertInstance.alert(ALERT_SUCCESS, 'toast.success.auth.success_reset_password');
                resolve(true);
            }).catch((error: any) => {
                if (process.env.NODE_ENV === 'development') console.error('API ERROR RESET PASSWORD: ' + error);
                reject(false);
            });       
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            reject(false);
        }
    });
}