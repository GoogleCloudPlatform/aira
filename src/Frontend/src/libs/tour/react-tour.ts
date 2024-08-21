import { STEP_EXAM_MIC_TESTER, STEP_EXAM_QUESTION_INFO, STEP_EXAM_RECORD_BUTTON_NEXT, STEP_EXAM_RECORD_BUTTON_PAUSE, STEP_EXAM_RECORD_BUTTON_START, STEP_EXAM_RECORD_BUTTON_STOP, STEP_EXAM_TIMER, STEP_EXAM_VISOR, STEP_EXAM_VISOR_EXPAND, STEP_TOUR_HELP_BUTTON } from "@/constants/tour";
import { IStep } from "@/interfaces/tour";
import { useTranslations } from "next-intl";

const STEPS_EXAM = [
    //STEP_EXAM_MIC_TESTER,
    STEP_EXAM_QUESTION_INFO,
    STEP_EXAM_VISOR,
    STEP_EXAM_VISOR_EXPAND,
    STEP_EXAM_TIMER,
    STEP_EXAM_RECORD_BUTTON_STOP,
    STEP_EXAM_RECORD_BUTTON_START,
    STEP_EXAM_RECORD_BUTTON_NEXT
];

const STEPS_TOUR = [
    STEP_TOUR_HELP_BUTTON
];

const STEPS = [...STEPS_EXAM];

const useReactTour = () => {
    const t = useTranslations('tour');

    const getSteps = (items : Array<string>) : Array<IStep> => {
        return Array.from(items, (item, index) => {
            return {
                selector: `[data-step=${item}]`,
                content: t(item) || "no_description",
            };
        });
    }

    return { getSteps };
}


export { STEPS_EXAM, STEPS_TOUR, STEPS, useReactTour };
