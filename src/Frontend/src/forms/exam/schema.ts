import { ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_WORDS } from "@/constants/enums";
import { IAnswer } from "@/interfaces/question";
import { isEmpty } from "lodash";
import { z } from "zod";

export const SchemaQuestionsCreation = z.object({
    order: z.number(),
    name: z.enum([ENUM_QUESTION_TYPE_WORDS, ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE]),
    type: z.enum([ENUM_QUESTION_TYPE_WORDS, ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE]),
    data: z.string({ required_error: "toast.errors.form.required_field" }).min(1, { message: "toast.errors.form.required_field" }),
    formatted_data: z.string(),
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
    name: z.enum([ENUM_QUESTION_TYPE_WORDS, ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE]),
    type: z.enum([ENUM_QUESTION_TYPE_WORDS, ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE]),
    data: z.string({ required_error: "toast.errors.form.required_field" }).min(1, { message: "toast.errors.form.required_field" }),
    formatted_data: z.string(),
    answers: z.union([
        z.undefined(),
        z.array(z.object({
            answer: z.string(),
            is_correct: z.boolean()
        }))
    ])
});

export const SchemaCreateExam = z.object({
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    questions: z.array(SchemaQuestionsCreation).nonempty({
        message: "toast.errors.form.cant_be_empty",
    }),
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

    const questionOneMaxSize = data.questions[0].data.trim().split(' ').length
    if (questionOneMaxSize > 60) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_one_max_size",
            path: ["questions"],
        })
    }

    const questionTwoMaxSize = data.questions[1].data.trim().split(' ').length
    if (questionTwoMaxSize > 40) {
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
        if (question.type === ENUM_QUESTION_TYPE_MULTIPLE_CHOICE && !question.answers) return true
        if (question.type === ENUM_QUESTION_TYPE_MULTIPLE_CHOICE && question.answers && question.answers?.length < 2) return true
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
        if (question.type !== ENUM_QUESTION_TYPE_MULTIPLE_CHOICE) return false
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

export const SchemaCreateExamDefaultValues : z.infer<typeof SchemaCreateExam> = {
    name: '',
    questions: [{
        order: 1,
        name: ENUM_QUESTION_TYPE_WORDS,
        type: ENUM_QUESTION_TYPE_WORDS,
        data: '',
        formatted_data: ''
    },
    {
        order: 2,
        name: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
        type: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
        data: '',
        formatted_data: ''
    },
    {
        order: 3,
        name: ENUM_QUESTION_TYPE_PHRASES,
        type: ENUM_QUESTION_TYPE_PHRASES,
        data: '',
        formatted_data: ''
    }
    ],
    grade: '',
    start_date: new Date(),
    end_date: new Date()
}

export const SchemaEditExam = z.object({
    id: z.string().uuid(),
    name: z.string().min(1, { message: "toast.errors.form.required_field" }),
    questions: z.array(SchemaQuestionsEdition).nonempty({
        message: "toast.errors.form.cant_be_empty",
    }),
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
    
    const questionOneMaxSize = data.questions[0].data.trim().split(' ').length
    if (questionOneMaxSize > 60) {
        ctx.addIssue({
            code: "custom",
            message: "toast.errors.form.question_one_max_size",
            path: ["questions"],
        })
    }

    const questionTwoMaxSize = data.questions[1].data.trim().split(' ').length
    if (questionTwoMaxSize > 40) {
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
        if (question.type === ENUM_QUESTION_TYPE_MULTIPLE_CHOICE && !question.answers) return true
        if (question.type === ENUM_QUESTION_TYPE_MULTIPLE_CHOICE && question.answers && question.answers?.length < 2) return true
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
        if (question.type !== ENUM_QUESTION_TYPE_MULTIPLE_CHOICE) return false
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

export const SchemaEditExamDefaultValues : z.infer<typeof SchemaEditExam> & { id: string, created_at: string, updated_at: string } = {
    id: '',
    name: '',
    questions: [{
        id: '',
        order: 1,
        name: ENUM_QUESTION_TYPE_WORDS,
        type: ENUM_QUESTION_TYPE_WORDS,
        data: '',
        formatted_data: ''
    },
    {
        id: '',
        order: 2,
        name: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
        type: ENUM_QUESTION_TYPE_COMPLEX_WORDS,
        data: '',
        formatted_data: ''
    },
    {
        id: '',
        order: 3,
        name: ENUM_QUESTION_TYPE_PHRASES,
        type: ENUM_QUESTION_TYPE_PHRASES,
        data: '',
        formatted_data: ''
    }
    ],
    grade: '',
    start_date: new Date(),
    end_date: new Date(),
    created_at: '',
    updated_at: ''
}