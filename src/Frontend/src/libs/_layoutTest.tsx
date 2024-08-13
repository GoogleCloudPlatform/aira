
export const layoutTester = async (searchParams: Record<string, string>) => {
    if (process.env.NODE_ENV !== 'development') {
        return;
    }
  
    if (typeof searchParams.loading !== 'undefined') {
        const loading = parseInt(searchParams.loading || '2000');
        await new Promise((resolve) => setTimeout(resolve, loading));
    }
  
    if (typeof searchParams.error !== 'undefined') {
        const error = searchParams.error || 'Something went wrong!';
        await new Promise((_resolve, reject) => reject(error));
    }
};