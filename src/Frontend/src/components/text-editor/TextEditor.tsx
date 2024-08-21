'use client';

import { withProps } from '@udecode/cn';
import { createPluginFactory, createPlugins, Plate, PlateElement, PlateLeaf, TElement } from '@udecode/plate-common';
import { createParagraphPlugin, ELEMENT_PARAGRAPH } from '@udecode/plate-paragraph';
import { createHeadingPlugin, ELEMENT_H1, ELEMENT_H2, ELEMENT_H3, ELEMENT_H4, ELEMENT_H5, ELEMENT_H6 } from '@udecode/plate-heading';
import { createBlockquotePlugin, ELEMENT_BLOCKQUOTE } from '@udecode/plate-block-quote';
import { createListPlugin, ELEMENT_UL, ELEMENT_OL, ELEMENT_LI } from '@udecode/plate-list';
import { createBoldPlugin, MARK_BOLD, createItalicPlugin, MARK_ITALIC, createUnderlinePlugin, MARK_UNDERLINE } from '@udecode/plate-basic-marks';
import { createKbdPlugin, MARK_KBD } from '@udecode/plate-kbd';
import { createAlignPlugin } from '@udecode/plate-alignment';
import { createIndentPlugin } from '@udecode/plate-indent';
import { createAutoformatPlugin } from '@udecode/plate-autoformat';
import { createNodeIdPlugin } from '@udecode/plate-node-id';

import { BlockquoteElement } from '@/components/plate-ui/blockquote-element';
import { HeadingElement } from '@/components/plate-ui/heading-element';
import { ListElement } from '@/components/plate-ui/list-element';
import { ParagraphElement } from '@/components/plate-ui/paragraph-element';
import { KbdLeaf } from '@/components/plate-ui/kbd-leaf';
import { Editor } from '@/components/plate-ui/editor';
import { FixedToolbar } from '@/components/plate-ui/fixed-toolbar';
import { FixedToolbarButtons } from '@/components/plate-ui/fixed-toolbar-buttons';
import { withPlaceholders } from '@/components/plate-ui/placeholder';
import { TooltipProvider } from '@/components/plate-ui/tooltip';
import { useTranslations } from 'next-intl';

interface TextEditorProps {
    data: string
    onChange: ( value: { data: string; formatted_data: string }) => void
}

const TextEditor: React.FC<TextEditorProps> = ({
    data,
    onChange
}) => {
    const t = useTranslations('text-editor')
    
    const initialValue = [
        {
            id: '1',
            type: 'p',
            align: 'left',
            children: [{ text: t('editor.write')}],
        },
    ];
    
    const saveTextPlugin = createPluginFactory({
        key: '',
        handlers: {
            onChange: (editor) => (value) => {
                const v = JSON.stringify(value)
                const i = JSON.stringify(initialValue)

                if (v !== i) {
                    const data = value.map((children: TElement) => children.children[0].text).join(' ').replace(/\s+/g, ' ')
                    const formatted_data = JSON.stringify(value)
                    onChange({data, formatted_data})
                }
            },
        },
    });

    const plugins:any = createPlugins(
        [
            saveTextPlugin(),
            createParagraphPlugin(),
            createHeadingPlugin(),
            createBlockquotePlugin(),
            createListPlugin(),
            createBoldPlugin(),
            createItalicPlugin(),
            createUnderlinePlugin(),
            createKbdPlugin(),
            createAlignPlugin({
                inject: {
                    props: {
                        validTypes: [
                            ELEMENT_PARAGRAPH,
                            ELEMENT_H1,
                            ELEMENT_H2,
                            ELEMENT_H3,
                            ELEMENT_H4,
                            ELEMENT_H5,
                            ELEMENT_H6,
                        ],
                    },
                },
            }),
            createIndentPlugin({
                inject: {
                    props: {
                        validTypes: [
                            ELEMENT_PARAGRAPH,
                            ELEMENT_H1,
                            ELEMENT_H2,
                            ELEMENT_H3,
                            ELEMENT_H4,
                            ELEMENT_H5,
                            ELEMENT_H6, ELEMENT_BLOCKQUOTE
                        ],
                    },
                },
            }),
            createAutoformatPlugin({
                options: {
                    rules: [
                        // Usage: https://platejs.org/docs/autoformat
                    ],
                    enableUndoOnDelete: true,
                },
            }),
            createNodeIdPlugin(),
        ],
        {
            components: withPlaceholders({
                [ELEMENT_BLOCKQUOTE]: BlockquoteElement,
                [ELEMENT_H1]: withProps(HeadingElement, { variant: 'h1' }),
                [ELEMENT_H2]: withProps(HeadingElement, { variant: 'h2' }),
                [ELEMENT_H3]: withProps(HeadingElement, { variant: 'h3' }),
                [ELEMENT_H4]: withProps(HeadingElement, { variant: 'h4' }),
                [ELEMENT_H5]: withProps(HeadingElement, { variant: 'h5' }),
                [ELEMENT_H6]: withProps(HeadingElement, { variant: 'h6' }),
                [ELEMENT_UL]: withProps(ListElement, { variant: 'ul' }),
                [ELEMENT_OL]: withProps(ListElement, { variant: 'ol' }),
                [ELEMENT_LI]: withProps(PlateElement, { as: 'li' }),
                [ELEMENT_PARAGRAPH]: ParagraphElement,
                [MARK_BOLD]: withProps(PlateLeaf, { as: 'strong' }),
                [MARK_ITALIC]: withProps(PlateLeaf, { as: 'em' }),
                [MARK_KBD]: KbdLeaf,
                [MARK_UNDERLINE]: withProps(PlateLeaf, { as: 'u' }),
            }),
        }
    );

    return (
        <TooltipProvider>
            <Plate plugins={plugins} initialValue={data.length > 0 ? data.charAt(0) === '[' && data.charAt(1) === '{' ? JSON.parse(data) : data : initialValue}>
                <FixedToolbar>
                    <FixedToolbarButtons />
                </FixedToolbar>
        
                <Editor />
            </Plate>
        </TooltipProvider>
    );
}

export default TextEditor