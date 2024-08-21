'use client';

import * as SeparatorPrimitive from '@radix-ui/react-separator';
import { withProps, withVariants } from '@udecode/cn';
import { cva } from 'class-variance-authority';

const separatorVariants = cva('shrink-0 bg-slate-200 dark:bg-slate-800', {
    variants: {
        orientation: {
            horizontal: 'h-px w-full',
            vertical: 'h-full w-px',
        },
    },
    defaultVariants: {
        orientation: 'horizontal',
    },
});

export const Separator = withVariants(
    withProps(SeparatorPrimitive.Root, {
        orientation: 'horizontal',
        decorative: true,
    }),
    separatorVariants
);
