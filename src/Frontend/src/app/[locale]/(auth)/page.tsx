'use client'
import { SignIn } from "@/components";
import Language from "@/components/language/Language";
import ThemeSwitch from "@/components/sign-in/ThemeSwitch";
import useTheme from "@/hooks/useTheme";
import Image from "next/image";
import { signinImage, signinLogoDark, signinLogoLight } from "../setup";

export default function Home() {
    const costumer = process.env.NEXT_PUBLIC_DEFAULT_THEME
    const { theme } = useTheme()
    const logo = theme ==='dark' ? signinLogoDark : signinLogoLight

    return (
        <main 
            className='w-full h-screen flex flex-col gap-1 lg:flex-row lg:gap-10 items-center justify-center bg-primary dark:bg-darkPrimary'
        >   
            <div className='hidden md:block absolute inset-0 overflow-hidden dark:hidden'>
                <svg
                    className='absolute inset-0'
                    viewBox='0 0 1440 320'
                    xmlns='http://www.w3.org/2000/svg'
                    preserveAspectRatio='none'
                >
                    <path
                        fill='#fff'
                        fillOpacity='1'
                        d='M0,192L60,202.7C120,213,240,235,360,229.3C480,224,600,192,720,170.7C840,149,960,139,1080,144C1200,149,1320,171,1380,181.3L1440,192L1440,0L1380,0C1320,0,1200,0,1080,0C960,0,840,0,720,0C600,0,480,0,360,0C240,0,120,0,60,0L0,0Z'
                    ></path>
                </svg>
            </div>

            <div className='relative z-10 hidden md:flex'>
                <Image
                    src={signinImage}
                    alt='signin-image'
                    width={500}
                    height={370}
                    priority
                    blurDataURL={signinImage}
                    quality={50}
                    className="max-w-[400px] lg:max-w-full max-h-[424px] w-auto h-auto"
                />
            </div>

            <section className='border border-border dark:border-darkBorder p-6 min-w-[360px] flex flex-col items-center rounded-md shadow-md shadow-black/20 gap-6 bg-background dark:bg-darkPrimary-foreground relative z-10'>
                <div className="absolute z-10 top-2 lg:-top-10 right-2 lg:right-0">
                    <ThemeSwitch/>
                </div>
                <div className="relative">
                    <Image
                        src={logo}
                        alt='logo'
                        width={150}
                        height={100}
                        style={{ width: `${costumer === 'SABER' ? '200px' : 'auto'}`, height: 'auto' }}
                        blurDataURL={logo}
                        priority
                    />
                </div>
                <SignIn />
            </section>
            <div className="absolute z-20 bottom-5 right-5">
                <Language type="login"/>
            </div>
        </main>
    );
}
