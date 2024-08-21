import React from 'react';
import { DropdownMenuProps } from '@radix-ui/react-dropdown-menu';
import { ELEMENT_BLOCKQUOTE } from '@udecode/plate-block-quote';
import {
    collapseSelection,
    findNode,
    focusEditor,
    isBlock,
    isCollapsed,
    TElement,
    toggleNodeType,
    useEditorRef,
    useEditorSelector,
} from '@udecode/plate-common';
import { ELEMENT_H1, ELEMENT_H2, ELEMENT_H3 } from '@udecode/plate-heading';
import { ELEMENT_PARAGRAPH } from '@udecode/plate-paragraph';

import { Icons } from '@/components/plate-ui/icons';

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuTrigger,
    useOpenState,
} from './dropdown-menu';
import { ToolbarButton } from './toolbar';
import { useTranslations } from 'next-intl';

const items = [
    {
        value: ELEMENT_PARAGRAPH,
        label: 'heading.p',
        description: 'heading.p',
        icon: Icons.paragraph,
    },
    {
        value: ELEMENT_H1,
        label: 'heading.h1',
        description: 'heading.h1',
        icon: Icons.h1,
    },
    {
        value: ELEMENT_H2,
        label: 'heading.h2',
        description: 'heading.h2',
        icon: Icons.h2,
    },
    {
        value: ELEMENT_H3,
        label: 'heading.h3',
        description: 'heading.h3',
        icon: Icons.h3,
    },
    {
        value: ELEMENT_BLOCKQUOTE,
        label: 'heading.quote',
        description: 'heading.quote-description',
        icon: Icons.blockquote,
    },
    {
        value: 'ul',
        label: 'heading.ul',
        description: 'heading.ul',
        icon: Icons.ul,
    },
    {
        value: 'ol',
        label: 'heading.ol',
        description: 'heading.ol',
        icon: Icons.ol,
    },
];

const defaultItem = items.find((item) => item.value === ELEMENT_PARAGRAPH)!;

export function TurnIntoDropdownMenu(props: DropdownMenuProps) {
    const t = useTranslations('text-editor')

    const value: string = useEditorSelector((editor) => {
        if (isCollapsed(editor.selection)) {
            const entry = findNode<TElement>(editor, {
                match: (n) => isBlock(editor, n),
            });

            if (entry) {
                return (
                    items.find((item) => item.value === entry[0].type)?.value ??
          ELEMENT_PARAGRAPH
                );
            }
        }

        return ELEMENT_PARAGRAPH;
    }, []);

    const editor = useEditorRef();
    const openState = useOpenState();

    const selectedItem =
    items.find((item) => item.value === value) ?? defaultItem;
    const { icon: SelectedItemIcon, label: selectedItemLabel } = selectedItem;

    return (
        <DropdownMenu modal={false} {...openState} {...props}>
            <DropdownMenuTrigger asChild>
                <ToolbarButton
                    pressed={openState.open}
                    tooltip={t('heading.size')}
                    isDropdown
                    className='lg:min-w-[130px] dark:text-white'
                >
                    <SelectedItemIcon className='size-5 lg:hidden' />
                    <span className='max-lg:hidden'>{t(selectedItemLabel)}</span>
                </ToolbarButton>
            </DropdownMenuTrigger>

            <DropdownMenuContent align='start' className='min-w-0'>
                <DropdownMenuLabel>{t('heading.size')}</DropdownMenuLabel>

                <DropdownMenuRadioGroup
                    className='flex flex-col gap-0.5'
                    value={value}
                    onValueChange={(type) => {
                        // if (type === 'ul' || type === 'ol') {
                        //   if (settingsStore.get.checkedId(KEY_LIST_STYLE_TYPE)) {
                        //     toggleIndentList(editor, {
                        //       listStyleType: type === 'ul' ? 'disc' : 'decimal',
                        //     });
                        //   } else if (settingsStore.get.checkedId('list')) {
                        //     toggleList(editor, { type });
                        //   }
                        // } else {
                        //   unwrapList(editor);
                        toggleNodeType(editor, { activeType: type });
                        // }

                        collapseSelection(editor);
                        focusEditor(editor);
                    }}
                >
                    {items.map(({ value: itemValue, label, icon: Icon }) => (
                        <DropdownMenuRadioItem
                            key={itemValue}
                            value={itemValue}
                            className='min-w-[180px]'
                        >
                            <Icon className='mr-2 size-5' />
                            {t(label)}
                        </DropdownMenuRadioItem>
                    ))}
                </DropdownMenuRadioGroup>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
