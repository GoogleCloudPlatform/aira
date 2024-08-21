import { ENUM_EXAM_STATUS_FINISHED } from "@/constants/enums";
import { IGroup } from "./group";
import { IQuestion } from "./question";

export interface IExamsResponse {
    items: Array<IExam>;
    pages: number;
    current_page: number;
    total: number;
}

export interface IExamResponse {
    id: string;
    questions: Array<IQuestion>;
    groups: Array<IGroup>;
    created_at: Date | string;
    updated_at: Date | string;
    start_date: Date | string;
    end_date: Date | string;
}

export interface IExam {
    id: string;
    name: string;
    data: string;
    grade: string;
    formatted_data: string;
    start_date: Date | string;
    end_date: Date | string;
    status?: typeof ENUM_EXAM_STATUS_FINISHED | string;
}