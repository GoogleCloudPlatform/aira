// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
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