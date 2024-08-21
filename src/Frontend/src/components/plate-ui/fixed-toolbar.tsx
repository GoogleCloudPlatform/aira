import { withCn } from '@udecode/cn';

import { Toolbar } from './toolbar';

export const FixedToolbar = withCn(
    Toolbar,
    'supports-backdrop-blur:bg-white/60 sticky left-0 top-[57px] z-50 w-full justify-between overflow-x-auto rounded-t-lg border-none bg-white/95 backdrop-blur dark:supports-backdrop-blur:bg-slate-950/60 dark:bg-zinc-900'
);
