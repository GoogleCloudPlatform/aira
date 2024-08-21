export const setCookie = (name: string, value: string, days: number = 1) => {
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + days);
  
    const cookieValue = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; expires=${expirationDate.toUTCString()}; path=/`;
  
    document.cookie = cookieValue;
};

export const getCookie = (name: string): string | null => {
    const decodedName = encodeURIComponent(name);
    const cookies = document.cookie.split(';');
  
    for (const cookie of cookies) {
        const trimmedCookie = cookie.trim();
        if (trimmedCookie.startsWith(`${decodedName}=`)) {
            const cookieValue = trimmedCookie.substring(decodedName.length + 1);
            return decodeURIComponent(cookieValue);
        }
    }
  
    return null;
};

export const clearCookie = (name: string): void => {
    const cookieValue = encodeURIComponent(name) + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = cookieValue;
};

