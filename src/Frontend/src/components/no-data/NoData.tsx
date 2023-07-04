import { useTranslation } from "react-i18next";

const NoData : React.FC<{ message?: string }> = ({ message = "no_data" }) => {
    const { t } = useTranslation();

    return (
        <>
            <div className='flex justify-center items-center p-1 md:p-10 w-full h-full overflow-x-hidden overflow-y-auto'>
                {t(message, { ns: "common" })}
            </div>
        </>
    );
}

export default NoData;