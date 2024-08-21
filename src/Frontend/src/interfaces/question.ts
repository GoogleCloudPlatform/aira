import { ENUM_EXAM_STATUS_FINISHED, ENUM_EXAM_STATUS_NOT_STARTED, ENUM_QUESTION_TYPE_COMPLEX_WORDS, ENUM_QUESTION_TYPE_MULTIPLE_CHOICE, ENUM_QUESTION_TYPE_PHRASES, ENUM_QUESTION_TYPE_WORDS } from "@/constants/enums";

export interface IAnswer {
    answer: string,
    is_correct: boolean
}

export interface IQuestionEditor {
    id?: string;
    order?: number;
    data: string;
    formatted_data: string;
    name: string;
    type: string;
    answers?: IAnswer[]
    status?: string;
}

export interface IQuestion {
    data: string;
    formatted_data: string;
    id: string;
    name: string;
    status: typeof ENUM_EXAM_STATUS_FINISHED | typeof ENUM_EXAM_STATUS_NOT_STARTED;
    start_date: Date | string;
    end_date: Date | string;
    type: typeof ENUM_QUESTION_TYPE_PHRASES | typeof ENUM_QUESTION_TYPE_WORDS | typeof ENUM_QUESTION_TYPE_COMPLEX_WORDS | typeof ENUM_QUESTION_TYPE_MULTIPLE_CHOICE
    response?: any;
    answers?: IAnswer[]
}

export interface IQuestionsResponse {
    
}

export interface IQuestionResponse {
    
}