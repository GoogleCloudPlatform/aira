import {notFound} from 'next/navigation';
import {getRequestConfig} from 'next-intl/server';
import { getMessages, i18n } from './libs/i18n/i18n-config';
 
// Can be imported from a shared config
const locales = i18n.locales;
 
export default getRequestConfig(async ({locale}) => {
    // Validate that the incoming `locale` parameter is valid
    if (!locales.includes(locale as any)) notFound();
 
    const messages = await getMessages(i18n.defaultLocale);
    return {
    //messages: (await import(`../messages/${locale}.json`)).default
        messages: messages
    };
});