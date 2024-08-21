"use client";

import { withProps } from "@udecode/cn";
import {
    createPlugins,
    Plate,
    PlateContent,
    PlateEditor,
    PlateElement,
    PlateLeaf,
    TElement,
    resetEditor,
    useEditorRef,
} from "@udecode/plate-common";
import {
    createParagraphPlugin,
    ELEMENT_PARAGRAPH,
} from "@udecode/plate-paragraph";
import {
    createHeadingPlugin,
    ELEMENT_H1,
    ELEMENT_H2,
    ELEMENT_H3,
    ELEMENT_H4,
    ELEMENT_H5,
    ELEMENT_H6,
} from "@udecode/plate-heading";
import {
    createBlockquotePlugin,
    ELEMENT_BLOCKQUOTE,
} from "@udecode/plate-block-quote";
import {
    createListPlugin,
    ELEMENT_UL,
    ELEMENT_OL,
    ELEMENT_LI,
} from "@udecode/plate-list";
import {
    createBoldPlugin,
    MARK_BOLD,
    createItalicPlugin,
    MARK_ITALIC,
    createUnderlinePlugin,
    MARK_UNDERLINE,
} from "@udecode/plate-basic-marks";
import { createKbdPlugin, MARK_KBD } from "@udecode/plate-kbd";
import { createAlignPlugin } from "@udecode/plate-alignment";
import { createIndentPlugin } from "@udecode/plate-indent";
import { createAutoformatPlugin } from "@udecode/plate-autoformat";
import { createNodeIdPlugin } from "@udecode/plate-node-id";

import { BlockquoteElement } from "@/components/plate-ui/blockquote-element";
import { HeadingElement } from "@/components/plate-ui/heading-element";
import { ListElement } from "@/components/plate-ui/list-element";
import { ParagraphElement } from "@/components/plate-ui/paragraph-element";
import { KbdLeaf } from "@/components/plate-ui/kbd-leaf";
import { withPlaceholders } from "@/components/plate-ui/placeholder";
import { TooltipProvider } from "@/components/plate-ui/tooltip";
import { useEffect, useMemo, useRef, useState } from "react";

interface TextVisorProps {
  data: string;
}

const plugins:any = createPlugins(
    [
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

const TextVisor: React.FC<TextVisorProps> = ({ data }) => {
    const isJSON = (str: string) => {
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            return false;
        }
    };

    const convertOldText = (str: string): TElement[] => {
        return [
            {
                id: "1",
                type: "p",
                children: [{ text: str }],
            },
        ];
    };

    const key = useMemo(() => {
        if (data) {
            return window.crypto.randomUUID();
        }
    }, [data]);

    if (!data) return null

    return (
        <TooltipProvider key={key}>
            <Plate
                plugins={plugins}
                initialValue={isJSON(data) ? JSON.parse(data) : convertOldText(data)}
                readOnly
            >
                <PlateContent  />
            </Plate>
        </TooltipProvider>
    );
};

export default TextVisor;
