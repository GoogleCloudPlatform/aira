const ShimmerActionTable : React.FC = () => {
    return (
        <>
            <div className="relative w-full flex flex-col gap-3">
                <div className="flex justify-end">
                    <button className="w-[100px] animate-pulse h-10 bg-gray-200 rounded-lg"></button>
                </div> 
                <div className="table h-[365px] w-full animate-pulse bg-gray-200 rounded-lg" />
                <div className="pagination flex items-center justify-between px-4 py-3 sm:px-6 bg-gray-200 animate-pulse rounded h-10" />
            </div>
        </>
    )
}

export default ShimmerActionTable;