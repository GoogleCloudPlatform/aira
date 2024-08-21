"use client";

import '@/styles/globals.css';
import { AuthProvider, PrivateRoute } from '@/context/auth';
import { Toast } from '@/components';
import useTheme from '@/hooks/useTheme';
import { PropsWithChildren } from 'react';
import { LoadingProvider } from '@/context/loading';
import { RBACProvider } from '@/context/rbac';
import { SCOPES } from '@/constants/rbac';
import { QueryClient,QueryClientProvider } from '@tanstack/react-query'
import { TourProvider } from '@reactour/tour';

// Create a client
const queryClient = new QueryClient()

export default function App({ children } : PropsWithChildren) {
    const { ThemeProvider } = useTheme();
    const radius = 10
    
    const app = (
        <>
            <ThemeProvider attribute="class" enableSystem={true}>
                <LoadingProvider>
                    <AuthProvider>
                        <PrivateRoute>
                            <RBACProvider roles={[]} scopes={[...SCOPES]}>
                                <QueryClientProvider client={queryClient}>
                                    <TourProvider 
                                        steps={[]}   
                                        styles={{
                                            popover: (base) => ({
                                                ...base,
                                                '--reactour-accent': '#ef5a3d',
                                                borderRadius: radius,
                                                color: "#000"
                                            }),
                                            maskArea: (base) => ({ ...base, rx: radius }),
                                            maskWrapper: (base) => ({ ...base, color: '#ef5a3d' }),
                                            badge: (base) => ({ ...base, left: 'auto', right: '-0.8125em' }),
                                            //controls: (base) => ({ ...base, marginTop: 100 }),
                                            close: (base) => ({ ...base, right: 'auto', left: 8, top: 8 }),
                                        }}
                                    >
                                        {children}
                                    </TourProvider>
                                </QueryClientProvider>
                            </RBACProvider>
                        </PrivateRoute>
                    </AuthProvider>
                    <Toast />
                </LoadingProvider>
            </ThemeProvider>
        </>
    );

    return app;
}