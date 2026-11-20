import { getRequestConfig } from 'next-intl/server';
import { getMessages, i18n } from './libs/i18n/i18n-config';

// Can be imported from a shared config
const locales = i18n.locales;

export default getRequestConfig(async ({ requestLocale }) => {
    let locale = await requestLocale;

    // Validate that the incoming `locale` parameter is valid
    if (!locale || !locales.includes(locale as any)) {
        locale = i18n.defaultLocale;
    }

    const messages = await getMessages(i18n.defaultLocale);
    return {
        locale,
        //messages: (await import(`../messages/${locale}.json`)).default
        messages: messages
    };
});