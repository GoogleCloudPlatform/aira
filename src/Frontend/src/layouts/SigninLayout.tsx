import { PropsWithChildren } from 'react';
import Head from 'next/head';
import { Header } from '@/components';
import Image from 'next/image';

export default function SigninLayout({ children } : PropsWithChildren<{}> ) {    
    
    return (
        <>
            <Head>
                <title>LIA</title>
                <meta name="description" content="LIA" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <div className='app flex flex-col h-screen'>
                <header className='h-[96px]'>
                    <Header />
                </header>
                <section className='flex flex-grow'>
                    <section className='w-8/12 h-full hidden md:flex'>    
                        <div className='w-full relative'>
                            <Image
                                src="/assets/images/intro.jpg" 
                                alt="intro" 
                                fill
                                sizes="(max-width: 768px) 80vw"
                                priority
                            />
                        </div>
                    </section>
                    <section className='w-full md:w-6/12 h-full'>
                        <main className='w-full flex flex-grow h-full flex-col'>
                            {children}
                        </main>
                    </section>
                </section>
            </div>
            
        </>
    )
}