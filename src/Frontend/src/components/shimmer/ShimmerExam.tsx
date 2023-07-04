const ShimmerExam : React.FC = () => {
    return (
        <>
            <div className="relative w-full h-full flex flex-col gap-3 p-5">
                <div className="flex justify-center">
                    <div className="animate-pulse bg-gray-200 w-[300px] h-[100px] rounded-lg"></div>
                </div>
                <div className="animate-pulse h-[400px] bg-gray-200 w-full rounded-lg"></div>
                <div className="flex gap-20 items-center justify-center mt-10">
                    <div className="animate-pulse h-[150px] w-[150px] bg-gray-200 rounded-full"></div>
                    <div className="animate-pulse h-[200px] w-[200px] bg-gray-200 rounded-full"></div>
                    <div className="animate-pulse h-[150px] w-[150px] bg-gray-200 rounded-full"></div>
                </div>
            </div>
        </>
    )
}

export default ShimmerExam;