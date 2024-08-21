'use client';

import * as React from 'react';
import * as ToolbarPrimitive from '@radix-ui/react-toolbar';
import { cn, withCn, withRef, withVariants } from '@udecode/cn';
import { cva, VariantProps } from 'class-variance-authority';

import { Icons } from '@/components/plate-ui/icons';

import { Separator } from './separator';
import { withTooltip } from './tooltip';

export const Toolbar = withCn(
    ToolbarPrimitive.Root,
    'relative flex select-none items-center gap-1 bg-white dark:bg-slate-950'
);

export const ToolbarToggleGroup = withCn(
    ToolbarPrimitive.ToolbarToggleGroup,
    'flex items-center'
);

export const ToolbarLink = withCn(
    ToolbarPrimitive.Link,
    'font-medium underline underline-offset-4'
);

export const ToolbarSeparator = withCn(
    ToolbarPrimitive.Separator,
    'my-1 w-px shrink-0 bg-slate-200 dark:bg-slate-800'
);

const toolbarButtonVariants = cva(
    cn(
        'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 dark:ring-offset-slate-950 dark:focus-visible:ring-slate-300',
        '[&_svg:not([data-icon])]:size-5 dark:text-white'
    ),
    {
        variants: {
            variant: {
                default:
          'bg-transparent hover:bg-slate-100 hover:text-slate-500 aria-checked:bg-slate-100 aria-checked:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-400 dark:aria-checked:bg-slate-800 dark:aria-checked:text-slate-50',
                outline:
          'border border-slate-200 bg-transparent hover:bg-slate-100 hover:text-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-50',
            },
            size: {
                default: 'h-10 px-3',
                sm: 'h-9 px-2',
                lg: 'h-11 px-5',
            },
        },
        defaultVariants: {
            variant: 'default',
            size: 'sm',
        },
    }
);

const ToolbarButton = withTooltip(
    // eslint-disable-next-line react/display-name
    React.forwardRef<
    React.ElementRef<typeof ToolbarToggleItem>,
    Omit<
      React.ComponentPropsWithoutRef<typeof ToolbarToggleItem>,
      'asChild' | 'value'
    > &
      VariantProps<typeof toolbarButtonVariants> & {
        pressed?: boolean;
        isDropdown?: boolean;
      }
  >(
      (
          { className, variant, size, isDropdown, children, pressed, ...props },
          ref
      ) => {
          return typeof pressed === 'boolean' ? (
              <ToolbarToggleGroup
                  type='single'
                  value='single'
                  disabled={props.disabled}
              >
                  <ToolbarToggleItem
                      ref={ref}
                      className={cn(
                          toolbarButtonVariants({
                              variant,
                              size,
                          }),
                          isDropdown && 'my-1 justify-between pr-1',
                          className
                      )}
                      value={pressed ? 'single' : ''}
                      {...props}
                  >
                      {isDropdown ? (
                          <>
                              <div className='flex flex-1'>{children}</div>
                              <div>
                                  <Icons.arrowDown className='ml-0.5 size-4' data-icon />
                              </div>
                          </>
                      ) : (
                          children
                      )}
                  </ToolbarToggleItem>
              </ToolbarToggleGroup>
          ) : (
              <ToolbarPrimitive.Button
                  ref={ref}
                  className={cn(
                      toolbarButtonVariants({
                          variant,
                          size,
                      }),
                      isDropdown && 'pr-1',
                      className
                  )}
                  {...props}
              >
                  {children}
              </ToolbarPrimitive.Button>
          );
      }
  )
);
ToolbarButton.displayName = 'ToolbarButton';
export { ToolbarButton };

export const ToolbarToggleItem = withVariants(
    ToolbarPrimitive.ToggleItem,
    toolbarButtonVariants,
    ['variant', 'size']
);

export const ToolbarGroup = withRef<
  'div',
  {
    noSeparator?: boolean;
  }
>(({ className, children, noSeparator }, ref) => {
    const childArr = React.Children.map(children, (c) => c);
    if (!childArr || childArr.length === 0) return null;

    return (
        <div ref={ref} className={cn('flex', className)}>
            {!noSeparator && (
                <div className='h-full py-1'>
                    <Separator orientation='vertical' />
                </div>
            )}

            <div className='mx-1 flex items-center gap-1'>{children}</div>
        </div>
    );
});
