'use client'

import useTheme from "@/hooks/useTheme";
import Image from "next/image";
import { signinLogoDark, signinLogoLight, costumer} from "../../setup";
import FormResetPassword from "@/forms/signin/FormResetPassword";

export default function Reset() {
    const { theme } = useTheme()
    const logo = theme ==='dark' ? signinLogoDark : signinLogoLight

    return (
        <main 
            className='w-full h-screen flex flex-col gap-1 lg:flex-row lg:gap-10 items-center justify-center bg-primary dark:bg-darkPrimary'
        >   
            <section className='border border-border dark:border-darkBorder p-6 min-w-[360px] flex flex-col items-center rounded-md shadow-md shadow-black/20 gap-6 bg-background dark:bg-darkPrimary-foreground relative z-10 py-14'>
                <Image
                    src={logo}
                    alt='logo'
                    width={150}
                    height={100}
                    style={{ width: `${costumer === 'SABER' ? '200px' : 'auto'}`, height: 'auto' }}
                    blurDataURL={logo}
                    priority
                />
                <FormResetPassword />
            </section>
        </main>
    );
}