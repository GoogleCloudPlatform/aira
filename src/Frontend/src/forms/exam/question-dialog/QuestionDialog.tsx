import React, { useState } from 'react'
import { useTranslations } from 'next-intl'
import { isEmpty } from 'lodash'
import { ControllerRenderProps } from 'react-hook-form'
import { IQuestionEditor } from '@/interfaces/question'
import { QuestionType } from '@/constants/enums'
import { useLoading } from '@/context/loading'

import QuestionsEditor from '@/components/visors/QuestionsEditor'
import { Button } from '@/components/ui/button'
import { Dialog, DialogTrigger, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { LucideCircleCheck, LucideCircleX } from 'lucide-react'
import { useQuestions } from '@/context/questions'

interface IQuestionDialogProps {
    question: IQuestionEditor
    field: ControllerRenderProps<any, any>
    index: number
    isEditable?: boolean
    preview?: boolean
}

const QuestionDialog: React.FC<IQuestionDialogProps> = ({ question, field, index, preview = false }) => {
    const [openQuestionDialog, setOpenQuestionDialog] = useState(false)
    const [openDeleteDialog, setOpenDeleteDialog] = useState(false)
    const { loading } = useLoading()

    const { type} = useQuestions()

    const t = useTranslations()

    const handleDeleteQuestion = (order: number) => {
        let updatedData = field.value

        if (question.type === QuestionType.Words || question.type === QuestionType.ComplexWords || question.type === QuestionType.Phrases) {
            updatedData = updatedData.filter((v: {type: QuestionType}) => v.type !== QuestionType.Words && v.type !== QuestionType.ComplexWords && v.type !== QuestionType.Phrases).map((v: IQuestionEditor, index: number) => ({...v, order: index + 1}))
        } else {
            updatedData = field.value.filter((v: {order: number}) => v.order !== order).map((v: IQuestionEditor, index: number) => ({...v, order: index + 1}))
        }

        field.onChange(updatedData)
        setOpenQuestionDialog(false)
        setOpenDeleteDialog(false)
    }

    return (
        <Dialog key={index} open={openQuestionDialog} onOpenChange={setOpenQuestionDialog}>
            <DialogTrigger className="py-2 px-4 border dark:border-darkBorder dark:text-white rounded-md text-sm w-full text-start">
                <div className="flex w-full justify-between items-center">
                    <span>{question.order} - {t(`form.exam.${question.type}`)}</span>
                    <i>
                        {!isEmpty(question.data) ? 
                            <LucideCircleCheck className="w-5 h-5 text-green-500" />
                            : 
                            <LucideCircleX className="w-5 h-5 text-destructive dark:text-darkDestructive" />
                        }
                    </i>
                </div>
            </DialogTrigger>
            <DialogContent style={{maxWidth: '1024px', minWidth: '90%', width: '90%'}} className="max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="dark:text-white">{t(`form.exam.${question.type}`)}</DialogTitle>
                    <DialogDescription>
                        {question.order} - {t(`form.exam.${question.type}`)}
                    </DialogDescription>
                </DialogHeader>

                <QuestionsEditor
                    question={question} 
                    field={field} 
                    index={index}
                    preview={preview}
                />
                <div className="w-full flex justify-end gap-4">
                    {type !== 'view' && (
                        <Dialog open={openDeleteDialog} onOpenChange={setOpenDeleteDialog}>
                            <DialogTrigger asChild>
                                <Button disabled={loading} type="button" variant="secondary" className="w-max text-white bg-destructive dark:bg-darkDestructive hover:bg-destructive/75 hover:dark:bg-darkDestructive/75">
                                    {t('form.exam.delete_question_button')}
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[425px]" aria-describedby="delete-dialog-desc">
                                <div id="delete-dialog-desc" className="sr-only">
                                    {t('form.exam.delete_question_description')}
                                </div>
                                <DialogHeader>
                                    <DialogTitle className="dark:text-white">{t('form.exam.delete_question_title')}</DialogTitle>
                                    <DialogDescription>{t('form.exam.delete_question_description')}</DialogDescription>
                                </DialogHeader>
                                <DialogFooter>
                                    <DialogClose asChild>
                                        <Button type="button" variant="secondary">
                                            {t('form.exam.close')}
                                        </Button>
                                    </DialogClose>
                                                                     
                                    <Button type="button" className=" text-white bg-destructive dark:bg-darkDestructive hover:bg-destructive/75 hover:dark:bg-darkDestructive/75" onClick={() => handleDeleteQuestion(question.order as number)}>{t('form.exam.delete_confirm')}</Button>
                                                                       
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}
                    
                    <DialogClose asChild>
                        <Button type="button" variant="secondary" className="w-max"> 
                            {preview ? t('form.exam.close') : t('form.exam.create.confirm')}
                        </Button>
                    </DialogClose>
                </div>
            </DialogContent>
        </Dialog> 
    )
}

export default QuestionDialog
