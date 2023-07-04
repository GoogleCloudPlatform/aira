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