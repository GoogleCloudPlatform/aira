import * as React from "react"

import { cn } from "@/libs/shadcn/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[60px] w-full rounded-md border border-input dark:border-darkInput bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground dark:placeholder:text-darkMuted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring dark:focus-visible:ring-darkRing disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
