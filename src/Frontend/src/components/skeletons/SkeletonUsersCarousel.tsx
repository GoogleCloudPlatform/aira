import { Skeleton } from "../ui/skeleton";

const SkeletonUsersCarousel : React.FC = () => {
    return (  
        <div className="mx-auto flex gap-6">
            {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="">
                    <div className="p-1">
                        <div className="flex aspect-square items-center justify-center p-2 h-[180px] w-[230px]"></div>
                    </div>
                </Skeleton>
            ))}
        </div>  

    )
}

export default SkeletonUsersCarousel;