import { Skeleton } from "../ui/skeleton";

const SkeletonExams : React.FC = () => {
    return (
        <>  
            <div className="wrapper sm:px-5 p-1 overflow-hidden">
                <div id="header" className="flex sm:flex-row flex-col gap-5 justify-between w-full">
                    <div className="space-x-2 gap-1 flex">
                        <Skeleton id="search" className="w-[300px] h-10" />
                        <Skeleton className="w-[100px]" />
                    </div>
                    <div className="grid grid-flow-col space-x-2">
                        <Skeleton className="sm:w-[90px] h-10" />
                        <Skeleton className="sm:w-[90px] h-10" />
                        <Skeleton className="sm:w-[90px] h-10" />
                    </div>
                </div>
                <div id="content">
                    <Skeleton className="h-[400px] w-full rounded-md mt-5"/>
                </div>
            </div>
        </>
    );
}

export default SkeletonExams;