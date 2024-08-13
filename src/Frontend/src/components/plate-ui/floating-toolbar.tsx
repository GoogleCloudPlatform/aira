'use client';

import React from 'react';
import { cn, withRef } from '@udecode/cn';
import { PortalBody, useComposedRef } from '@udecode/plate-common';
import {
    flip,
    FloatingToolbarState,
    offset,
    useFloatingToolbar,
    useFloatingToolbarState,
} from '@udecode/plate-floating';

import { Toolbar } from './toolbar';

export const FloatingToolbar = withRef<
  typeof Toolbar,
  {
    state?: FloatingToolbarState;
  }
>(({ state, children, ...props }, componentRef) => {
    const floatingToolbarState = useFloatingToolbarState({
        ...state,
        floatingOptions: {
            placement: 'top',
            middleware: [
                offset(12),
                flip({
                    padding: 12,
                    fallbackPlacements: [
                        'top-start',
                        'top-end',
                        'bottom-start',
                        'bottom-end',
                    ],
                }),
            ],
            ...state?.floatingOptions,
        },
    });

    const {
        ref: floatingRef,
        props: rootProps,
        hidden,
    } = useFloatingToolbar(floatingToolbarState);

    const ref = useComposedRef<HTMLDivElement>(componentRef, floatingRef);

    if (hidden) return null;

    return (
        <PortalBody>
            <Toolbar
                ref={ref}
                className={cn(
                    'absolute z-50 whitespace-nowrap border border-slate-200 bg-white px-1 opacity-100 shadow-md print:hidden dark:border-slate-800 dark:bg-slate-950'
                )}
                {...rootProps}
                {...props}
            >
                {children}
            </Toolbar>
        </PortalBody>
    );
});
