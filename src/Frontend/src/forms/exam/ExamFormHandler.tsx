
import React, { Dispatch, SetStateAction } from 'react'
import { TActionSheetOptions } from '@/interfaces/component'
import { QuestionsProvider } from '@/context/questions';
import FormCreateExam from './FormCreateExam';
import FormEditExam from './FormEditExam';

const ExamFormHandler = ({ options, setOpen }: { options: TActionSheetOptions; setOpen: Dispatch<SetStateAction<boolean>>; }) => {
    return (
        <QuestionsProvider type={options.mode}>
            {options.mode === 'create' && ( <FormCreateExam formData={options.formData} setOpen={setOpen} /> )}
            {options.mode === 'edit' && ( <FormEditExam {...options} setOpen={setOpen} /> )}
            {options.mode === 'view' && ( <FormEditExam {...options} setOpen={setOpen} preview={true} /> )}
        </QuestionsProvider>
    )
}

export default ExamFormHandler
