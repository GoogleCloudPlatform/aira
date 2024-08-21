import HomePage from "@/components/home";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { homeMetadata } from "../../setup";
import Loading from "@/components/loading/Loading";

export const metadata = homeMetadata

export default async function Home() {
    return (
        <>
            <ErrorBoundary fallback={<p>⚠️Something went wrong</p>}>
                <Suspense fallback={<Loading style="vertical" text={true}/>}>
                    <HomePage />
                </Suspense>
            </ErrorBoundary>
        </>
    )
}