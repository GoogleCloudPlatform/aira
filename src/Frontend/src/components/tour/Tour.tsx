import { useEffect } from "react";
import { useTour } from "@reactour/tour";
import { useReactTour } from "@/libs/tour/react-tour";
import { STEP_TOUR_HELP_BUTTON } from "@/constants/tour";
import { Button } from "../ui/button";
import { LucideMessageCircleQuestion } from "lucide-react";


type TTourProps = {
    steps: Array<string>,
}

const Tour : React.FC<TTourProps> = ({ steps }) => {
    const { setIsOpen, setSteps, setCurrentStep } = useTour();
    const { getSteps } = useReactTour();

    // set tour steps
    useEffect(() => {
        if (setSteps) setSteps(getSteps(steps));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [setSteps, steps]); // disabled and not included on array dep to avoid loop render

    return (
        <>
            <div data-step={STEP_TOUR_HELP_BUTTON} className='absolute bottom-0 right-0 md:bottom-2 md:right-2 z-50 shadow-2xl'>
                <Button
                    variant={"ghost"}
                    size={"icon"}
                    className="text-primary dark:text-white"
                    onClick={() => {
                        if (setSteps) setSteps(getSteps(steps));
                        setCurrentStep(0);
                        setIsOpen(true);
                    }}
                >
                    <LucideMessageCircleQuestion />
                </Button>
            </div>
        </>
    )
}

export default Tour;