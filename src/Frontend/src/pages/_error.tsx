import Error from 'next/error';

function Page({ statusCode }: any) {
    return <Error statusCode={statusCode}></Error>;
}

Page.getInitialProps = ({ res, err }: { res: any; err: any }) => {
    const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
    return { statusCode };
};

export default Page;