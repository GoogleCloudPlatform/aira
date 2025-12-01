import { ENUM_EXAM_STATUS_FINISHED, ENUM_EXAM_STATUS_NOT_STARTED, QuestionTheme, QuestionType } from "@/constants/enums";

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
    theme: QuestionTheme | null;
}

export interface IQuestion {
    data: string;
    formatted_data: string;
    id: string;
    name: string;
    status: typeof ENUM_EXAM_STATUS_FINISHED | typeof ENUM_EXAM_STATUS_NOT_STARTED;
    start_date: Date | string;
    end_date: Date | string;
    type: QuestionType;
    response?: any;
    answers?: IAnswer[]
    theme: QuestionTheme | null;
}

export interface IQuestionsResponse {
    
}

export interface IQuestionResponse {
    
}

export interface IGenerateWordsQuestionResponse {
    words: string[]
}

export interface IGenerateMultipleChoiceQuestionResponse {
    question: string,
    answers: IAnswer[]
}

export interface IGenerateQuestionsResponse {
    question: string,
}