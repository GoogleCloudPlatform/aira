import { Skeleton } from "../ui/skeleton";

const SkeletonHome : React.FC = () => {
    return (
        <>
            <div id="wrapper">
                <div className="flex flex-col gap-5 p-2">
                    <Skeleton className="h-[270px] w-full" />
                    <Skeleton className="h-[100px] w-full" />
                    <Skeleton className="h-[230px] w-full" />
                    <Skeleton className="h-[230px] w-full" />
                </div>
            </div>
        </>
    )
}

export default SkeletonHome;