import { api } from "@/api/api";
import { getURL } from "@/utils";
import { IGenerateMultipleChoiceQuestionResponse, IGenerateQuestionsResponse, IGenerateWordsQuestionResponse } from "@/interfaces/question";
import { ENDPOINT_PROCESSOR_GENERATE_MULTIPLE_CHOICE, ENDPOINT_PROCESSOR_GENERATE_QUESTION, ENDPOINT_PROCESSOR_GENERATE_TEXT, ENDPOINT_PROCESSOR_GENERATE_WORDS } from "@/constants/endpoints";
import { QuestionTheme, QuestionType } from "@/constants/enums";

export async function getWordsQuestion(qty_words: number, words: string[], question_type: QuestionType) : Promise<IGenerateWordsQuestionResponse> {
    return new Promise<IGenerateWordsQuestionResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_PROCESSOR_GENERATE_WORDS, { qty_words, words, question_type }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            // if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            if (process.env.NODE_ENV === 'development') console.log('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getTextQuestion(subject?: string) : Promise<string> {
    return new Promise<string>(async (resolve, reject) => {
        try {
            const url = getURL(ENDPOINT_PROCESSOR_GENERATE_TEXT, { subject: subject ? subject : '' });
            await api.get(url).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            // if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            if (process.env.NODE_ENV === 'development') console.log('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getMultipleChoiceQuestion(qty_options: number, user_input: string, text_data: string, block_questions: string[] | null) : Promise<IGenerateMultipleChoiceQuestionResponse> {
    return new Promise<IGenerateMultipleChoiceQuestionResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_PROCESSOR_GENERATE_MULTIPLE_CHOICE, { qty_options, user_input, text_data, block_questions }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            // if (process.env.NODE_ENV === 'development') console.error('PROMISE ERROR: ' + e);
            if (process.env.NODE_ENV === 'development') console.log('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}

export async function getQuestions(question_type: string, user_input: string, text_data: string, block_questions: string[] | null, theme: QuestionTheme | null) : Promise<IGenerateQuestionsResponse> {
    return new Promise<IGenerateQuestionsResponse>(async (resolve, reject) => {
        try {
            await api.post(ENDPOINT_PROCESSOR_GENERATE_QUESTION, { question_type, user_input, text_data, block_questions, question_theme: theme }).then(response => {
                resolve(response.data);
            });
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.log('PROMISE ERROR: ' + e);
            reject(null);
        }
    });
}