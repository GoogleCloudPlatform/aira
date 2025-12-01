import { z } from "zod";
import { isEmpty } from "lodash";
import { addDays } from "date-fns";
import { IAnswer } from "@/interfaces/question";
import { QuestionTheme, QuestionType, THIRD_HIGH_SCHOOL } from "@/constants/enums";

export const SchemaQuestionsCreation = z.object({
    order: z.number(),
    name: z.nativeEnum(QuestionType),
    type: z.nativeEnum(QuestionType),
    data: z.string({ required_error: "toast.errors.form.required_field" }).min(1, { message: "toast.errors.form.required_field" }),
    formatted_data: z.string(),
    theme: z.nativeEnum(QuestionTheme).nullable(),
    answers: z.union([
        z.undefined(),
        z.array(z.object({
            answer: z.string(),
            is_correct: z.boolean()
        }))
    ])
});

export const SchemaQuestionsEdition = z.object({
    id: z.string().uuid().optional(),
    order: z.number(),
    name: z.nativeEnum(QuestionType),
    type: z.nativeEnum(QuestionType),
    data: z.string({ required_error: "toast.errors.form.required_field" }).min(1, { message: "toast.errors.form.required_field" }),
    formatted_data: z.string(),
    theme: z.nativeEnum(QuestionTheme).nullable(),
    answers: z.union([
        z.null(),
        z.undefined(),
        z.array(z.object({
            answer: z.string(),
            is_correct: z.boolean()
        }))
    ])
});

export const SchemaCreateExam = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    questions: z.array(SchemaQuestionsCreation),
    grade: z.string().min(1, { message: "toast.errors.form.required_field" }),
    start_date: z.date(),
    end_date: z.date(),
}).superRefine((data, ctx) => {
    if (data.end_date <= data.start_date) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.end_date_cannot_be_earlier",
            path: ["end_date"],
        })
    }

    const questionOneMaxSize = data?.questions[0]?.data.trim().split(' ').length
    if (data?.questions[0]?.type === QuestionType.Words && questionOneMaxSize > 60) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_one_max_size",
            path: ["questions"],
        })
    }

    const questionTwoMaxSize = data?.questions[1]?.data.trim().split(' ').length
    if (data?.questions[1]?.type === QuestionType.ComplexWords && questionTwoMaxSize > 40) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_two_max_size",
            path: ["questions"],
        })
    }

    const hasEmptyQuestions = data.questions.some(question => isEmpty(question.data));
    if (hasEmptyQuestions) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.empty_questions",
            path: ["questions"],
        })
    }

    const hasEmptyAnswers = data.questions.some(question => {
        if (question.type === QuestionType.MultipleChoice && !question.answers) return true
        if (question.type === QuestionType.MultipleChoice && question.answers && question.answers?.length < 2) return true
        return false
    });
    
    if (hasEmptyAnswers) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.empty_answers",
            path: ["questions"],
        })
    }
    
    const missingTrue = data.questions.some(question => {
        if (question.type !== QuestionType.MultipleChoice) return false
        if (!question.answers) return false

        const check = question.answers.some((item: IAnswer) => item.is_correct === true )
        if (!check) return true

        return false
    });

    if (missingTrue) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.missing_true",
            path: ["questions"],
        })
    }
})

export const SchemaEditExam = z.object({
    id: z.string().uuid(),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    questions: z.array(SchemaQuestionsEdition),
    grade: z.string().min(1, { message: "toast.errors.form.required_field" }),
    start_date: z.date(),
    end_date: z.date(),
}).superRefine((data, ctx) => {
    if (data.end_date <= data.start_date) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.end_date_cannot_be_earlier",
            path: ["end_date"],
        })
    }
    
    const questionOneMaxSize = data?.questions[0]?.data.trim().split(' ').length
    if (data?.questions[0]?.type === QuestionType.Words && questionOneMaxSize > 60) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_one_max_size",
            path: ["questions"],
        })
    }

    const questionTwoMaxSize = data?.questions[1]?.data.trim().split(' ').length
    if (data?.questions[1]?.type === QuestionType.ComplexWords && questionTwoMaxSize > 40) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_two_max_size",
            path: ["questions"],
        })
    }

    const hasEmptyQuestions = data.questions.some(question => isEmpty(question.data));
    if (hasEmptyQuestions) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.empty_questions",
            path: ["questions"],
        })
    }

    const hasEmptyAnswers = data.questions.some(question => {
        if (question.type === QuestionType.MultipleChoice && !question.answers) return true
        if (question.type === QuestionType.MultipleChoice && question.answers && question.answers?.length < 2) return true
        return false
    });
    
    if (hasEmptyAnswers) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.empty_answers",
            path: ["questions"],
        })
    }
    
    const missingTrue = data.questions.some(question => {
        if (question.type !== QuestionType.MultipleChoice) return false
        if (!question.answers) return false

        const check = question.answers.some((item: IAnswer) => item.is_correct === true )
        if (!check) return true

        return false
    });

    if (missingTrue) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.missing_true",
            path: ["questions"],
        })
    }

    return ctx.path
})

export const SchemaCreateExamDefaultValues : z.infer<typeof SchemaCreateExam> = {
    name: '',
    questions: [],
    grade: THIRD_HIGH_SCHOOL,
    start_date: addDays(new Date(), 1),
    end_date: addDays(new Date(), 8),
}

export const SchemaEditExamDefaultValues : z.infer<typeof SchemaEditExam> & { id: string, created_at: string, updated_at: string } = {
    id: '',
    name: '',
    questions: [],
    grade: THIRD_HIGH_SCHOOL,
    start_date: addDays(new Date(), 1),
    end_date: addDays(new Date(), 8),
    created_at: '',
    updated_at: ''
}