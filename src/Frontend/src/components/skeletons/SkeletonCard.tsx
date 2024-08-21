import { Skeleton } from "../ui/skeleton";

const SkeletonCard : React.FC = () => {
    return (
        <Skeleton className="w-full lg:max-w-72 cursor-pointer h-48 rounded-[12px] shadow-sm shadow-black/20 bg-black/5 dark:bg-white/10 overflow-hidden" />
    )
}

export default SkeletonCard;