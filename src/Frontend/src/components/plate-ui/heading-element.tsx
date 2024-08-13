import React from 'react';
import { withRef, withVariants } from '@udecode/cn';
import { PlateElement } from '@udecode/plate-common';
import { cva } from 'class-variance-authority';

const headingVariants = cva('', {
    variants: {
        variant: {
            h1: 'mb-1 mt-[2em] font-heading text-4xl font-bold dark:text-white',
            h2: 'mb-px mt-[1.4em] font-heading text-2xl font-semibold tracking-tight dark:text-white',
            h3: 'mb-px mt-[1em] font-heading text-xl font-semibold tracking-tight dark:text-white',
            h4: 'mt-[0.75em] font-heading text-lg font-semibold tracking-tight dark:text-white',
            h5: 'mt-[0.75em] text-lg font-semibold tracking-tight dark:text-white',
            h6: 'mt-[0.75em] text-base font-semibold tracking-tight dark:text-white',
        },
        isFirstBlock: {
            true: 'mt-0',
            false: '',
        },
    },
});

const HeadingElementVariants = withVariants(PlateElement, headingVariants, [
    'isFirstBlock',
    'variant',
]);

export const HeadingElement = withRef<typeof HeadingElementVariants>(
    ({ variant = 'h1', isFirstBlock, children, ...props }, ref) => {
        const { element, editor } = props;

        const Element = variant!;

        return (
            <HeadingElementVariants
                ref={ref}
                asChild
                variant={variant}
                isFirstBlock={element === editor.children[0]}
                {...props}
            >
                <Element>{children}</Element>
            </HeadingElementVariants>
        );
    }
);
