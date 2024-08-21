import { Skeleton } from "../ui/skeleton";

const SkeletonResults : React.FC = () => {
    return (
        <>
            <div className="relative w-auto h-full flex flex-col gap-3 p-5">
                <Skeleton className="w-[170px] h-[35px] rounded-lg" />
                <Skeleton className="h-[100px] rounded-md" />

                <div className="flex flex-col gap-2 mt-10">
                    {Array.from({ length: 3 }, (_, index) => <Skeleton key={index} className="rounded-md w-full h-[150px]" />)}
                </div>
            </div>
        </>
    );
}

export default SkeletonResults;