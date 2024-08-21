import { LoaderCircle } from "lucide-react";
import { useTranslations } from "next-intl";

type Props = {
    style?: 'horizontal' | 'vertical';
    size?: number;
    text?: boolean; 
    color?: string;
}

const Loading : React.FC<Props> = ({ text, size, style, color }) => {
    const t = useTranslations()

    return (
        <div className={`${style === 'vertical' && 'flex-col'} flex items-center justify-center gap-2`}>
            <LoaderCircle className={`animate-spin ${ color ? color : 'text-blue-500 dark:text-white'}`} size={size ? size : 40}/>
            {text && (
                <span className="text-blue-500 dark:text-white">{t('loading') + "..."}</span>
            )}
        </div>
    );
}

export default Loading;