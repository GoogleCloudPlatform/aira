import { Skeleton } from "../ui/skeleton";

const SkeletonSheet : React.FC = () => {
    return (
        <>
            <div id="wrapper">
                <div className="flex flex-col gap-3">
                    <Skeleton className="h-[500px] w-full rounded-md" />
                    <Skeleton className="h-10 w-[120px] self-end flex" />
                </div>
            </div>
        </>
    );
}

export default SkeletonSheet;