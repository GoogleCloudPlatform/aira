import Load from "@/components/loading/Loading"

const Loading = () => {
    return (
        <section className='flex min-w-full h-screen justify-center items-center'>
            <Load style="vertical" text={true}/>
        </section>
    ) 
}

export default Loading