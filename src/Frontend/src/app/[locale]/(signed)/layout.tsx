import { Header } from "@/components"
import { homeMetadata } from "../setup";

export const metadata = homeMetadata

export default async function Layout({ children } : { children: React.ReactNode }) {
    return (
        <main className='relative h-full w-full flex flex-col md:flex-row bg-background dark:bg-darkBackground text-white overflow-hidden'>
            <header>
                <Header />
            </header>
            
            <section className="w-full h-full p-2 overflow-hidden">
                {children}
            </section>
        </main>
    )
}
