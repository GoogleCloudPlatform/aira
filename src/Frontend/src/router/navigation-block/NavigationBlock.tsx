// keeping track on nextjs team oficial response https://github.com/vercel/next.js/discussions/41934#discussioncomment-8996669
// there is not yet a way to get popstate on next13+

// components/navigation-block.tsx
'use client';

import {
    Dispatch,
    PropsWithChildren,
    SetStateAction,
    createContext,
    useContext,
    useEffect,
    useRef,
    useState,
} from 'react';

const NavigationBlockerContext = createContext<
  [isBlocked: boolean, setBlocked: Dispatch<SetStateAction<boolean>>]
>([false, () => {}]);

export function NavigationBlockerProvider({
    children,
}: {
  children: React.ReactNode;
}) {
    // [isBlocked, setBlocked]
    const state = useState(false);
    return (
        <NavigationBlockerContext.Provider value={state}>
            {children}
        </NavigationBlockerContext.Provider>
    );
}

export function useIsBlocked() {
    const [isBlocked, setBlocked] = useContext(NavigationBlockerContext);
    return isBlocked;
}

export function Blocker() {
    const [isBlocked, setBlocked] = useContext(NavigationBlockerContext);
    useEffect(() => {
        setBlocked(() => {
            return true;
        });
        return () => {
            setBlocked(() => {
                return false;
            });
        };
    }, [isBlocked, setBlocked]);
    return null;
}

export function BlockBrowserNavigation() {
    const isBlocked = useIsBlocked();
    useEffect(() => {
        if (process.env.NODE_ENV === 'development') console.log({ isBlocked });
        if (isBlocked) {
            const showModal = (event: BeforeUnloadEvent) => {
                event.preventDefault();
            };

            window.addEventListener('beforeunload', showModal);
            return () => {
                window.removeEventListener('beforeunload', showModal);
            };
        }
    }, [isBlocked]);

    return null;
}

export function useBackButtonNavigation(handler: (event: Event) => void) {
    const isBlocked = useIsBlocked();
    const enabled = typeof handler === 'function';

    // Persist handler in ref
    const handlerRef = useRef(handler);
    useEffect(() => {
        handlerRef.current = handler;
    });

    useEffect(() => {
        if (process.env.NODE_ENV === 'development') console.log({ isBlocked });
        if (enabled && isBlocked) {
            // keeping track on nextjs team oficial response so far - https://github.com/vercel/next.js/discussions/41934#discussioncomment-8996669
            // there is not yet a way to get popstate on next13+
            window.history.pushState(null, '', ''); // caveat to allow backbutton click - not the best solution

            const listener = (event: PopStateEvent) => {
                handlerRef.current(event);
                window.history.pushState(null, '', window.location.href); // preventing forward button
                return false;
            };

            window.addEventListener('popstate', listener);
            return () => {
                window.removeEventListener('popstate', listener);
            };
        }
    }, [enabled, isBlocked]);

    return null;
}