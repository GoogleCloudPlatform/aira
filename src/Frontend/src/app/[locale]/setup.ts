import { Metadata } from "next";

export const costumer = process.env.NEXT_PUBLIC_DEFAULT_THEME

const APP_NAME = 'AIRA';
const APP_DESCRIPTION = `${APP_NAME} Application`

export const signinLogoLight = '/assets/images/logo.png'
export const signinLogoDark = '/assets/images/logo.png'
export const sidebarLogoLight = '/assets/images/logo.png'
export const sidebarLogoDark = '/assets/images/logo.png'

export const signinImage = '/assets/images/intro.png'

export const sidebarLogoSize = 'w-[200px]'

export const appMetadata : Metadata = {
    title: APP_NAME,
    description: APP_DESCRIPTION,
    applicationName: APP_NAME,
    appleWebApp: {
        capable: true,
        title: APP_NAME,
        statusBarStyle: "default",
    },
    formatDetection: {
        telephone: false,
    },
    // themeColor: "#FFFFFF",
    // viewport: "minimum-scale=1, initial-scale=1, width=device-width, shrink-to-fit=no, viewport-fit=cover",
    //manifest: "/manifest.json",
    icons: [
        // { rel: "apple-touch-icon", url: "/apple-touch-icon.png" },
        { rel: "shortcut icon", url: `favicon.ico` },
    ],
    keywords: [`aira`],
};

export const homeMetadata : Metadata = {
    title: `${APP_NAME} - Home`,
    description: 'Home page',
}

export const studentsMetadata = {
    title:  `${APP_NAME} - Students`,
    description: 'Students',
}

export const resultsMetadata = {
    title:  `${APP_NAME} - Results`,
    description: 'Results',
}

export const reportsMetadata = {
    title:  `${APP_NAME} - Dashboard`,
    description: 'Dashboard',
}

export const groupsMetadata = {
    title:  `${APP_NAME} - Groups`,
    description: 'Groups',
}

export const examsMetadata = {
    title: `${APP_NAME} - Exams `,
    description: 'Exams',
}

export const examQuestionsMetadata = {
    title: `${APP_NAME} - Exam Questions`,
    description: 'Exams',
}

export const examFinishMetadata = {
    title: `${APP_NAME} - Exam Finish`,
    description: 'Exams',
}

export const usersMetadata = {
    title:  `${APP_NAME} - Users`,
    description: 'Users',
}

export const organizationsMetadata = {
    title:  `${APP_NAME} - Organizations`,
    description: 'Organizations',
}

export const resetPasswordMetadata = {
    title:  `${APP_NAME} - Reset Password`,
    description: 'Reset Password',
}