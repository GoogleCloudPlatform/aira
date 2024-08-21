import { Skeleton } from "../ui/skeleton";

const SkeletonExam : React.FC = () => {
    return (
        <>
            <div className="relative w-full h-full flex flex-col gap-3 p-5">
                <div className="flex justify-center">
                    <Skeleton className="w-[300px] h-[100px] rounded-lg" />
                </div>

                <Skeleton className="h-[450px] w-full rounded-lg" />

                <div className="flex gap-20 items-center justify-center mt-10">
                    <Skeleton className="h-[150px] w-[150px] rounded-full" />
                    <Skeleton className="h-[200px] w-[200px] rounded-full" />
                    <Skeleton className="h-[150px] w-[150px] rounded-full" />
                </div>
            </div>
        </>
    )
}

export default SkeletonExam;