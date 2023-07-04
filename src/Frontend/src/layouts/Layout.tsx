import { PropsWithChildren } from 'react';
import Head from 'next/head';
import { Navbar } from '@/components';

export default function Layout({ children } : PropsWithChildren<{}> ) {        
    return (
        <>
            <Head>
                <title>LIA</title>
                <meta name="description" content="LIA" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <div className='app h-screen flex flex-col'>
                <header className='sm:h-[96px] h-[64px]'>
                    <Navbar />
                </header>
                <section className='flex sm:h-[calc(100vh-96px)] h-[calc(100vh-64px)] w-full'>    
                    <main className='h-full w-full'>
                        {children}        
                    </main>
                </section>
            </div>
            
        </>
    )
}