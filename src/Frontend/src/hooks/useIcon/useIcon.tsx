import { ICON_ARROW_RIGHT, ICON_MICROPHONE, ICON_STOP, ICON_ARROW_PATH, ICON_PENCIL, ICON_TRASH, ICON_PLUS, ICON_BUILDING_LIBRARY, ICON_USER_GROUP, ICON_X_MARK, ICON_EXCLAMATION_TRIANGLE, ICON_ARROW_LEFT, ICON_CHEVRON_LEFT, ICON_CHEVRON_RIGHT, ICON_USER, ICON_PENCIL_SQUARE, ICON_ACADEMIC_CAP, ICON_EYE, ICON_LANGUAGE, ICON_TABLE_CELLS, ICON_BARS_3, ICON_ARROW_LEFT_ON_RECTANGLE, ICON_HOME, ICON_DOCUMENT_TEXT, ICON_COG, ICON_CHEVRON_DOWN, ICON_USER_CIRCLE, ICON_ELLIPSIS_VERTICAL, ICON_PRESENTATION_CHART_BAR, ICON_CHART_PIE, ICON_ARROWS_POINTING_OUT, ICON_ARROWS_POINTING_IN, ICON_MAGNIFYING_GLASS } from "@/constants/icons";
import { IIcon } from "@/interfaces/icons";
import { MicrophoneIcon, StopIcon, ArrowRightIcon, ArrowPathIcon, TrashIcon, PencilIcon, PlusIcon, BuildingLibraryIcon, UserGroupIcon, XMarkIcon, ExclamationTriangleIcon, ArrowLeftIcon, ChevronLeftIcon, ChevronRightIcon, UserIcon, PencilSquareIcon, AcademicCapIcon, EyeIcon, LanguageIcon, TableCellsIcon, Bars3Icon, ArrowLeftOnRectangleIcon, HomeIcon, DocumentTextIcon, CogIcon, ChevronDownIcon, UserCircleIcon, EllipsisVerticalIcon, PresentationChartBarIcon, ChartPieIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon, MagnifyingGlassIcon } from "@heroicons/react/24/solid";
import { PropsWithChildren } from "react";

const useIcon = () => {

    const getSize = () => 'w-full h-full';
    
    const getIcon = ({ icon, action, classes } : IIcon) => {
        let newIcon = null;

        if (icon === ICON_MICROPHONE) newIcon = <MicrophoneIcon />;
        if (icon === ICON_STOP) newIcon = <StopIcon />;
        if (icon === ICON_ARROW_LEFT) newIcon = <ArrowLeftIcon />;
        if (icon === ICON_ARROW_RIGHT) newIcon = <ArrowRightIcon />;
        if (icon === ICON_ARROW_PATH) newIcon = <ArrowPathIcon />
        if (icon === ICON_PENCIL) newIcon = <PencilIcon />
        if (icon === ICON_TRASH) newIcon = <TrashIcon />
        if (icon === ICON_PLUS) newIcon = <PlusIcon />
        if (icon === ICON_BUILDING_LIBRARY) newIcon = <BuildingLibraryIcon />
        if (icon === ICON_USER_GROUP) newIcon = <UserGroupIcon />
        if (icon === ICON_X_MARK) newIcon = <XMarkIcon />
        if (icon === ICON_EXCLAMATION_TRIANGLE) newIcon = <ExclamationTriangleIcon />
        if (icon === ICON_CHEVRON_LEFT) newIcon = <ChevronLeftIcon />
        if (icon === ICON_CHEVRON_RIGHT) newIcon = <ChevronRightIcon />
        if (icon === ICON_USER) newIcon = <UserIcon />
        if (icon === ICON_PENCIL_SQUARE) newIcon = <PencilSquareIcon />
        if (icon === ICON_ACADEMIC_CAP) newIcon = <AcademicCapIcon />
        if (icon === ICON_EYE) newIcon = <EyeIcon />
        if (icon === ICON_TABLE_CELLS) newIcon = <TableCellsIcon />
        if (icon === ICON_LANGUAGE) newIcon = <LanguageIcon />
        if (icon === ICON_BARS_3) newIcon = <Bars3Icon />
        if (icon === ICON_ARROW_LEFT_ON_RECTANGLE) newIcon = <ArrowLeftOnRectangleIcon />
        if (icon === ICON_HOME) newIcon = <HomeIcon />
        if (icon === ICON_DOCUMENT_TEXT) newIcon = <DocumentTextIcon />
        if (icon === ICON_COG) newIcon = <CogIcon />
        if (icon === ICON_CHEVRON_DOWN) newIcon = <ChevronDownIcon />
        if (icon === ICON_USER_CIRCLE) newIcon = <UserCircleIcon />
        if (icon === ICON_ELLIPSIS_VERTICAL) newIcon = <EllipsisVerticalIcon />
        if (icon === ICON_PRESENTATION_CHART_BAR) newIcon = <PresentationChartBarIcon />
        if (icon === ICON_CHART_PIE) newIcon = <ChartPieIcon />
        if (icon === ICON_ARROWS_POINTING_OUT) newIcon = <ArrowsPointingOutIcon />
        if (icon === ICON_ARROWS_POINTING_IN) newIcon = <ArrowsPointingInIcon />
        if (icon === ICON_MAGNIFYING_GLASS) newIcon = <MagnifyingGlassIcon />

      
        const CustomIcon = ({ action, children } : PropsWithChildren<{ action: () => void }>) => (
            <div onClick={action} className={`${classes ? classes : ''} ${getSize()}`}>
                {children}
            </div>
        )

        return (
            <CustomIcon action={action ? action : () => null}>
                {newIcon}
            </CustomIcon>
        );
    
    }

    return { getIcon }
}

export default useIcon;
