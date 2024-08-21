import React from 'react';
import {
    MARK_BOLD,
    MARK_CODE,
    MARK_ITALIC,
    MARK_STRIKETHROUGH,
    MARK_UNDERLINE,
} from '@udecode/plate-basic-marks';
import { useEditorReadOnly } from '@udecode/plate-common';

import { Icons } from '@/components/plate-ui/icons';

import { InsertDropdownMenu } from './insert-dropdown-menu';
import { MarkToolbarButton } from './mark-toolbar-button';
import { ModeDropdownMenu } from './mode-dropdown-menu';
import { ToolbarGroup } from './toolbar';
import { TurnIntoDropdownMenu } from './turn-into-dropdown-menu';
import { AlignDropdownMenu } from './align-dropdown-menu';
import { useTranslations } from 'next-intl';

export function FixedToolbarButtons() {
    const readOnly = useEditorReadOnly();
    const t = useTranslations('text-editor')

    return (
        <div className='w-full overflow-hidden'>
            <div
                className='flex flex-wrap'
                style={{
                    transform: 'translateX(calc(-1px))',
                }}
            >
                {!readOnly && (
                    <>
                        <ToolbarGroup noSeparator>
                            <TurnIntoDropdownMenu />
                        </ToolbarGroup>

                        <ToolbarGroup className='dark:text-white '>
                            <MarkToolbarButton tooltip={t('toolbar.bold')} nodeType={MARK_BOLD}>
                                <Icons.bold />
                            </MarkToolbarButton>
                            <MarkToolbarButton tooltip={t('toolbar.italic')} nodeType={MARK_ITALIC}>
                                <Icons.italic />
                            </MarkToolbarButton>
                            <MarkToolbarButton
                                tooltip={t('toolbar.underline')}
                                nodeType={MARK_UNDERLINE}
                            >
                                <Icons.underline />
                            </MarkToolbarButton>
                        </ToolbarGroup>


                        <ToolbarGroup noSeparator>
                            <AlignDropdownMenu />
                        </ToolbarGroup>
                    </>
                )}
                
                <div className='grow' />

                <ToolbarGroup noSeparator>
                    <ModeDropdownMenu />
                </ToolbarGroup>
            </div>
        </div>
    );
}
