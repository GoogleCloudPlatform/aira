// components/link.tsx
'use client';

import { startTransition, useState } from 'react';
import NextLink from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useIsBlocked } from '../navigation-block/NavigationBlock';
import LeavePageDialog from '../leave-page-dialog/LeavePageDialog';
import { usePaginationStore } from '@/store/pagination';
import { IPaginationStore } from '@/interfaces/store';

/**
 * A custom Link component that wraps Next.js's next/link component.
 */
export function Link({
    href,
    children,
    replace,
    ...rest
}: Parameters<typeof NextLink>[0]) {
    const router = useRouter();
    const isBlocked = useIsBlocked();
    const [showLeaveDialog, setShowLeaveDialog] = useState<boolean>(false);
    const { setPagination } : IPaginationStore = usePaginationStore();
    const params = useParams()

    const goTo = () => {
        if (href === '/users/exams') {
            setPagination("show_finished", false);
        }

        const tutorial_path = process.env.NEXT_PUBLIC_TUTORIAL_BUCKET
        if (tutorial_path && String(href).includes(tutorial_path)) {
            return window.open(`${href}`, '_blank')
        }

        startTransition(() => {
            let url = new URL(href.toString(), window.location.origin);
            // add locale to URL
            url.pathname = `/${params.locale}${url.pathname}`;

            if (replace) {
                router.replace(url.toString());
            } else {
                router.push(url.toString());
            }
        });
        setShowLeaveDialog(false);
    }

    return (
        <>
            <NextLink
                href={href}
                onClick={(e) => {
                    e.preventDefault();

                    if (isBlocked) {
                        setShowLeaveDialog(true);
                        return;
                    }

                    goTo();
                }}
                {...rest}
            >
                {children}
            </NextLink>

            <LeavePageDialog 
                open={showLeaveDialog}
                onOpenChange={setShowLeaveDialog}
                onConfirmation={goTo}
            />
        </>
    );
}