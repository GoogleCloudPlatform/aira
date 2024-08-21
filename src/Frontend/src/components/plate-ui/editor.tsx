import React from 'react';
import { cn } from '@udecode/cn';
import { PlateContent } from '@udecode/plate-common';
import { cva } from 'class-variance-authority';

import type { PlateContentProps } from '@udecode/plate-common';
import type { VariantProps } from 'class-variance-authority';

const editorVariants = cva(
    cn(
        'relative overflow-x-auto whitespace-pre-wrap break-words',
        'min-h-[80px] w-full rounded-md bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none dark:bg-zinc-900 dark:ring-offset-slate-950 dark:placeholder:text-slate-400',
        '[&_[data-slate-placeholder]]:text-slate-500 [&_[data-slate-placeholder]]:!opacity-100 dark:[&_[data-slate-placeholder]]:text-slate-400',
        '[&_[data-slate-placeholder]]:top-[auto_!important]',
        '[&_strong]:font-bold',
        'min-h-[300px] max-h-[50vh]',
        'dark:text-white'
    ),
    {
        variants: {
            variant: {
                outline: 'border border-border dark:border-darkBorder',
                ghost: '',
            },
            focused: {
                true: 'ring-2 ring-slate-950 ring-offset-2 dark:ring-slate-300',
            },
            disabled: {
                true: 'cursor-not-allowed opacity-50',
            },
            focusRing: {
                true: 'focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 dark:focus-visible:ring-slate-300',
                false: '',
            },
            size: {
                sm: 'text-sm',
                md: 'text-base',
            },
        },
        defaultVariants: {
            variant: 'outline',
            focusRing: true,
            size: 'sm',
        },
    }
);

export type EditorProps = PlateContentProps &
  VariantProps<typeof editorVariants>;

const Editor = React.forwardRef<HTMLDivElement, EditorProps>(
    (
        {
            className,
            disabled,
            focused,
            focusRing,
            readOnly,
            size,
            variant,
            ...props
        },
        ref
    ) => {
        return (
            <div ref={ref} className='relative w-full'>
                <PlateContent
                    className={cn(
                        editorVariants({
                            disabled,
                            focused,
                            focusRing,
                            size,
                            variant,
                        }),
                        className
                    )}
                    disableDefaultStyles
                    readOnly={disabled ?? readOnly}
                    aria-disabled={disabled}
                    {...props}
                />
            </div>
        );
    }
);
Editor.displayName = 'Editor';

export { Editor };
