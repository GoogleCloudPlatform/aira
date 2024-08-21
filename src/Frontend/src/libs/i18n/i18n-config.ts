export const defaultLocale = 'en-US';
export const locales = ['en-US', 'pt-BR', 'es-ES']; 

export const i18n = {
    defaultLocale: defaultLocale,
    locales: locales,
} as const;
  
export type Locale = (typeof i18n)['locales'][number];

export const getMessages = async (locale : Locale) => {
    if (!locales.includes(locale as any)) return;
    return {
        ...(await import(`./languages/${locale}/common.json`)).default,
        ...(await import(`./languages/${locale}/dialog.json`)).default,
        ...(await import(`./languages/${locale}/exam.json`)).default,
        ...(await import(`./languages/${locale}/home.json`)).default,
        ...(await import(`./languages/${locale}/text-editor.json`)).default,
        ...(await import(`./languages/${locale}/preview.json`)).default,
        ...(await import(`./languages/${locale}/tour.json`)).default,
        ...(await import(`./languages/${locale}/form.json`)).default,
        ...(await import(`./languages/${locale}/toast.json`)).default,
        ...(await import(`./languages/${locale}/results.json`)).default,
    }
}