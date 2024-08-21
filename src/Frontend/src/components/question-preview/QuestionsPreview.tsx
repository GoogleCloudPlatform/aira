import React, { useState } from 'react'
import { Drawer, DrawerClose, DrawerContent, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer";
import { Button } from '../ui/button';
import { IQuestionEditor } from '@/interfaces/question';
import { useTranslations } from 'next-intl';
import { isEmpty } from 'lodash';
import QuestionsVisor from '../visors/QuestionsVisor';

interface QuestionPreviewProps {
    questions: Array<IQuestionEditor>
}

const QuestionsPreview: React.FC<QuestionPreviewProps> = ({ questions }) => {
    const [questionIndex, setQuestionIndex] = useState(0)

    const data = questions.filter((q:IQuestionEditor) => !isEmpty(q.data))
    const t = useTranslations('preview');

    const handleChangeQuestion = (type: string) => {
        setQuestionIndex(prev => type === 'next' ? prev + 1 : prev - 1)
    }

    if (!data || isEmpty(data) || !data[questionIndex]) return null;

    return (
        <Drawer>
            <DrawerTrigger asChild>
                <Button variant="secondary" className="w-full" disabled={data.length === 0}>
                    {t('buttons.preview')}
                </Button>
            </DrawerTrigger>
            <DrawerContent className="h-full">
                <DrawerHeader>
                    <DrawerTitle className='dark:text-white'>{t('titles.preview_title_start')} {t(`questions.${data[questionIndex].type}`)} {t('titles.preview_title_end')}</DrawerTitle>
                </DrawerHeader>

                <div className='flex flex-col px-4 py-1 lg:p-6 justify-between h-full'>  
                    <div className='overflow-y-auto max-h-[60vh]'>
                        <QuestionsVisor question={data[questionIndex]} />
                    </div>      
          
                    {data.length > 1 && (
                        <div className='w-full mt-5 flex justify-center items-center gap-4'>
                            <Button variant="outline" className='w-32' onClick={() => handleChangeQuestion('prev')} disabled={questionIndex <= 0}>
                                {t('buttons.previous')}
                            </Button>
                            <Button variant="outline" className='w-32' onClick={() => handleChangeQuestion('next')} disabled={questionIndex >= data.length - 1}>
                                {t('buttons.next')}
                            </Button>
                        </div>
                    )}
                </div>

                <DrawerFooter>
                    <DrawerClose asChild>
                        <Button variant="secondary">
                            {t('buttons.close')}
                        </Button>
                    </DrawerClose>
                </DrawerFooter>
            </DrawerContent>
        </Drawer>  
    )
}

export default QuestionsPreview;